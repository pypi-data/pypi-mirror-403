"""
Utility functions for Snowflake resources.
"""
from __future__ import annotations
import re
import decimal
import base64
from numbers import Number
from datetime import datetime, date
from typing import List, Any, Dict, cast

from .... import dsl
from ....environments import runtime_env, SnowbookEnvironment

# warehouse-based snowflake notebooks currently don't have hazmat
crypto_disabled = False
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
except (ModuleNotFoundError, ImportError):
    crypto_disabled = True

# Constants used by helper functions
ENGINE_ERRORS = ("engine is suspended", "create/resume", "engine not found", "no engines found", "engine was deleted")
ENGINE_NOT_READY_MSGS = ("engine is in pending", "engine is provisioning")
DATABASE_ERRORS = ("database not found",)

# Constants for import/export and transaction processing
VALID_IMPORT_STATES = ("PENDING", "PROCESSING", "QUARANTINED", "LOADED")
IMPORT_STREAM_FIELDS = (
    "ID", "CREATED_AT", "CREATED_BY", "STATUS", "REFERENCE_NAME", "REFERENCE_ALIAS",
    "FQ_OBJECT_NAME", "RAI_DATABASE", "RAI_RELATION", "DATA_SYNC_STATUS",
    "PENDING_BATCHES_COUNT", "NEXT_BATCH_STATUS", "NEXT_BATCH_UNLOADED_TIMESTAMP",
    "NEXT_BATCH_DETAILS", "LAST_BATCH_DETAILS", "LAST_BATCH_UNLOADED_TIMESTAMP", "CDC_STATUS"
)
FIELD_MAP = {
    "database_name": "database",
    "engine_name": "engine",
}


def process_jinja_template(template: str, indent_spaces: int = 0, **substitutions: Any) -> str:
    """Process a Jinja-like template.

    Supports:
    - Variable substitution {{ var }}
    - Conditional blocks {% if condition %} ... {% endif %}
    - For loops {% for item in items %} ... {% endfor %}
    - Comments {# ... #}
    - Whitespace control with {%- and -%}

    Args:
        template: The template string
        indent_spaces: Number of spaces to indent the result
        **substitutions: Variable substitutions
    """

    def evaluate_condition(condition: str, context: dict) -> bool:
        """Safely evaluate a condition string using the context."""
        # Replace variables with their values
        for k, v in context.items():
            if isinstance(v, str):
                condition = condition.replace(k, f"'{v}'")
            else:
                condition = condition.replace(k, str(v))
        try:
            return bool(eval(condition, {"__builtins__": {}}, {}))
        except Exception:
            return False

    def process_expression(expr: str, context: dict) -> str:
        """Process a {{ expression }} block."""
        expr = expr.strip()
        if expr in context:
            return str(context[expr])
        return ""

    def process_block(lines: List[str], context: dict, indent: int = 0) -> List[str]:
        """Process a block of template lines recursively."""
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle comments
            line = re.sub(r'{#.*?#}', '', line)

            # Handle if blocks
            if_match = re.search(r'{%\s*if\s+(.+?)\s*%}', line)
            if if_match:
                condition = if_match.group(1)
                if_block = []
                else_block = []
                i += 1
                nesting = 1
                in_else_block = False
                while i < len(lines) and nesting > 0:
                    if re.search(r'{%\s*if\s+', lines[i]):
                        nesting += 1
                    elif re.search(r'{%\s*endif\s*%}', lines[i]):
                        nesting -= 1
                    elif nesting == 1 and re.search(r'{%\s*else\s*%}', lines[i]):
                        in_else_block = True
                        i += 1
                        continue

                    if nesting > 0:
                        if in_else_block:
                            else_block.append(lines[i])
                        else:
                            if_block.append(lines[i])
                    i += 1
                if evaluate_condition(condition, context):
                    result.extend(process_block(if_block, context, indent))
                else:
                    result.extend(process_block(else_block, context, indent))
                continue

            # Handle for loops
            for_match = re.search(r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}', line)
            if for_match:
                var_name, iterable_name = for_match.groups()
                for_block = []
                i += 1
                nesting = 1
                while i < len(lines) and nesting > 0:
                    if re.search(r'{%\s*for\s+', lines[i]):
                        nesting += 1
                    elif re.search(r'{%\s*endfor\s*%}', lines[i]):
                        nesting -= 1
                    if nesting > 0:
                        for_block.append(lines[i])
                    i += 1
                if iterable_name in context and isinstance(context[iterable_name], (list, tuple)):
                    for item in context[iterable_name]:
                        loop_context = dict(context)
                        loop_context[var_name] = item
                        result.extend(process_block(for_block, loop_context, indent))
                continue

            # Handle variable substitution
            line = re.sub(r'{{\s*(\w+)\s*}}', lambda m: process_expression(m.group(1), context), line)

            # Handle whitespace control
            line = re.sub(r'{%-', '{%', line)
            line = re.sub(r'-%}', '%}', line)

            # Add line with proper indentation, preserving blank lines
            if line.strip():
                result.append(" " * (indent_spaces + indent) + line)
            else:
                result.append("")

            i += 1

        return result

    # Split template into lines and process
    lines = template.split('\n')
    processed_lines = process_block(lines, substitutions)

    return '\n'.join(processed_lines)


def type_to_sql(type_obj: Any) -> str:
    if type_obj is str:
        return "VARCHAR"
    if type_obj is int:
        return "NUMBER"
    if type_obj is Number:
        return "DECIMAL(38, 15)"
    if type_obj is float:
        return "FLOAT"
    if type_obj is decimal.Decimal:
        return "DECIMAL(38, 15)"
    if type_obj is bool:
        return "BOOLEAN"
    if type_obj is dict:
        return "VARIANT"
    if type_obj is list:
        return "ARRAY"
    if type_obj is bytes:
        return "BINARY"
    if type_obj is datetime:
        return "TIMESTAMP"
    if type_obj is date:
        return "DATE"
    if isinstance(type_obj, dsl.Type):
        return "VARCHAR"
    raise ValueError(f"Unknown type {type_obj}")


def type_to_snowpark(type_obj: Any) -> str:
    if type_obj is str:
        return "StringType()"
    if type_obj is int:
        return "IntegerType()"
    if type_obj is float:
        return "FloatType()"
    if type_obj is Number:
        return "DecimalType(38, 15)"
    if type_obj is decimal.Decimal:
        return "DecimalType(38, 15)"
    if type_obj is bool:
        return "BooleanType()"
    if type_obj is dict:
        return "MapType()"
    if type_obj is list:
        return "ArrayType()"
    if type_obj is bytes:
        return "BinaryType()"
    if type_obj is datetime:
        return "TimestampType()"
    if type_obj is date:
        return "DateType()"
    if isinstance(type_obj, dsl.Type):
        return "StringType()"
    raise ValueError(f"Unknown type {type_obj}")


def sanitize_user_name(user: str) -> str:
    """Sanitize a user name by extracting the part before '@' and replacing invalid characters."""
    # Extract the part before the '@'
    sanitized_user = user.split('@')[0]
    # Replace any character that is not a letter, number, or underscore with '_'
    sanitized_user = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized_user)
    return sanitized_user


def is_engine_issue(response_message: str) -> bool:
    """Check if a response message indicates an engine issue."""
    return any(kw in response_message.lower() for kw in ENGINE_ERRORS + ENGINE_NOT_READY_MSGS)


def is_database_issue(response_message: str) -> bool:
    """Check if a response message indicates a database issue."""
    return any(kw in response_message.lower() for kw in DATABASE_ERRORS)


def collect_error_messages(e: Exception) -> list[str]:
    """Collect all error messages from an exception and its chain.

    Extracts messages from:
    - str(e)
    - e.message (if present, e.g., RAIException)
    - e.args (string arguments)
    - e.__cause__
    - e.__context__
    - Nested JavaScript execution errors
    """
    messages = [str(e).lower()]

    # Check message attribute (RAIException has this)
    if hasattr(e, 'message'):
        msg = getattr(e, 'message', None)
        if isinstance(msg, str):
            messages.append(msg.lower())

    # Check args
    if hasattr(e, 'args') and e.args:
        for arg in e.args:
            if isinstance(arg, str):
                messages.append(arg.lower())

    # Check cause and context
    if hasattr(e, '__cause__') and e.__cause__:
        messages.append(str(e.__cause__).lower())
    if hasattr(e, '__context__') and e.__context__:
        messages.append(str(e.__context__).lower())

    # Extract nested messages from JavaScript execution errors
    for msg in messages[:]:  # Copy to avoid modification during iteration
        if re.search(r"javascript execution error", msg):
            matches = re.findall(r'"message"\s*:\s*"([^"]+)"', msg, re.IGNORECASE)
            messages.extend([m.lower() for m in matches])

    return messages


#--------------------------------------------------
# Parameter and Data Transformation Utilities
#--------------------------------------------------

def normalize_params(params: List[Any] | Any | None) -> List[Any] | None:
    """Normalize parameters to a list format."""
    if params is not None and not isinstance(params, list):
        return cast(List[Any], [params])
    return params


def format_sproc_name(name: str, type_obj: Any) -> str:
    """Format stored procedure parameter name based on type."""
    if type_obj is datetime:
        return f"{name}.astimezone(ZoneInfo('UTC')).isoformat(timespec='milliseconds')"
    return name


def is_azure_url(url: str) -> bool:
    """Check if a URL is an Azure blob storage URL."""
    return "blob.core.windows.net" in url


def is_container_runtime() -> bool:
    """Check if running in a container runtime environment."""
    return isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "container"


#--------------------------------------------------
# Import/Export Utilities
#--------------------------------------------------

def is_valid_import_state(state: str) -> bool:
    """Check if an import state is valid."""
    return state in VALID_IMPORT_STATES


def imports_to_dicts(results: List[Any]) -> List[Dict[str, Any]]:
    """Convert import results to dictionaries with lowercase keys."""
    parsed_results = [
        {field.lower(): row[field] for field in IMPORT_STREAM_FIELDS}
        for row in results
    ]
    return parsed_results


#--------------------------------------------------
# Transaction Utilities
#--------------------------------------------------

def txn_list_to_dicts(transactions: List[Any]) -> List[Dict[str, Any]]:
    """Convert transaction list to dictionaries with field mapping."""
    dicts = []
    for txn in transactions:
        dict = {}
        txn_dict = txn.asDict()
        for key in txn_dict:
            mapValue = FIELD_MAP.get(key.lower())
            if mapValue:
                dict[mapValue] = txn_dict[key]
            else:
                dict[key.lower()] = txn_dict[key]
        dicts.append(dict)
    return dicts


#--------------------------------------------------
# Encryption Utilities
#--------------------------------------------------

def decrypt_stream(key: bytes, iv: bytes, src: bytes) -> bytes:
    """Decrypt the provided stream with PKCS#5 padding handling."""
    if crypto_disabled:
        if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "warehouse":
            raise Exception("Please open the navigation-bar dropdown labeled *Packages* and select `cryptography` under the *Anaconda Packages* section, and then re-run your query.")
        else:
            raise Exception("library `cryptography.hazmat` missing; please install")

    # `type:ignore`s are because of the conditional import, which
    # we have because warehouse-based snowflake notebooks don't support
    # the crypto library we're using.
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())  # type: ignore
    decryptor = cipher.decryptor()

    # Decrypt the data
    decrypted_padded_data = decryptor.update(src) + decryptor.finalize()

    # Unpad the decrypted data using PKCS#5
    unpadder = padding.PKCS7(128).unpadder()  # type: ignore # Use 128 directly for AES
    unpadded_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    return unpadded_data


def decrypt_artifact(data: bytes, encryption_material: str) -> bytes:
    """Decrypts the artifact data using provided encryption material."""
    encryption_material_parts = encryption_material.split("|")
    assert len(encryption_material_parts) == 3, "Invalid encryption material"

    algorithm, key_base64, iv_base64 = encryption_material_parts
    assert algorithm == "AES_128_CBC", f"Unsupported encryption algorithm {algorithm}"

    key = base64.standard_b64decode(key_base64)
    iv = base64.standard_b64decode(iv_base64)

    return decrypt_stream(key, iv, data)

