# Azure import is dropped because we need to to do runtime import of azure module to support our package running on Snowflake Notebook
from . import config

# Lazy imports for client and local to avoid circular import issues
# These modules import from relationalai which imports from clients, creating a cycle
def __getattr__(name: str):
    if name == 'client':
        from . import client
        return client
    elif name == 'local':
        from . import local
        return local
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# note: user must do `import relationalai.clients.azure` to get `azure` submodule
# note: snowflake module is now at relationalai.clients.resources.snowflake
# note: 'client' and 'local' are lazy-loaded via __getattr__, so they're not in __all__
__all__ = ['config']
