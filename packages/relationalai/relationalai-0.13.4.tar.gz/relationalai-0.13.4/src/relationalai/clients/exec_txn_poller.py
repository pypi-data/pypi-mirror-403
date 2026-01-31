from __future__ import annotations

import time
from typing import Dict, Optional, TYPE_CHECKING

from relationalai import debugging
from relationalai.clients.util import poll_with_specified_overhead
from relationalai.tools.cli_controls import create_progress
from relationalai.util.format import format_duration

if TYPE_CHECKING:
    from relationalai.clients.resources.snowflake import Resources

# Polling behavior constants
POLL_OVERHEAD_RATE = 0.1  # Overhead rate for exponential backoff

# Text color constants
GREEN_COLOR = '\033[92m'
GRAY_COLOR = '\033[90m'
ENDC = '\033[0m'


class ExecTxnPoller:
    """
    Encapsulates the polling logic for exec_async transaction completion.
    """

    def __init__(
        self,
        print_txn_progress: bool,
        resource: "Resources",
        txn_id: Optional[str] = None,
        headers: Optional[Dict] = None,
        txn_start_time: Optional[float] = None,
    ):
        self.print_txn_progress = print_txn_progress
        self.res = resource
        self.txn_id = txn_id
        self.headers = headers or {}
        self.txn_start_time = txn_start_time or time.time()

    def __enter__(self) -> ExecTxnPoller:
        if not self.print_txn_progress:
            return self
        self.progress = create_progress(
            description=lambda: self.description_with_timing(),
            success_message="",  # We'll handle this ourselves
            leading_newline=False,
            trailing_newline=False,
            show_duration_summary=False,
        )
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if not self.print_txn_progress or self.txn_id is None:
            return
        # Update to success message with duration
        total_duration = time.time() - self.txn_start_time
        txn_id = self.txn_id
        self.progress.update_main_status(
            query_complete_message(txn_id, total_duration)
        )
        self.progress.__exit__(exc_type, exc_value, traceback)
        return

    def poll(self) -> bool:
        """
        Poll for transaction completion with interactive progress display.

        Returns:
            True if transaction completed successfully, False otherwise
        """
        if not self.txn_id:
            raise ValueError("Transaction ID must be provided for polling.")
        else:
            txn_id = self.txn_id

        if self.print_txn_progress:
            # Update the main status to include the new txn_id
            self.progress.update_main_status_fn(
                lambda: self.description_with_timing(txn_id),
            )

        # Don't show duration summary - we handle our own completion message
        def check_status() -> bool:
            """Check if transaction is complete."""
            finished = self.res._check_exec_async_status(txn_id, headers=self.headers)
            return finished

        with debugging.span("wait", txn_id=self.txn_id):
            poll_with_specified_overhead(check_status, overhead_rate=POLL_OVERHEAD_RATE)


        return True

    def description_with_timing(self, txn_id: str | None = None) -> str:
        elapsed = time.time() - self.txn_start_time
        if txn_id is None:
            return query_progress_header(elapsed)
        else:
            return query_progress_message(txn_id, elapsed)

def query_progress_header(duration: float) -> str:
    # Don't print sub-second decimals, because it updates too fast and is distracting.
    duration_str = format_duration(duration, seconds_decimals=False)
    return f"Evaluating Query... {duration_str:>15}\n"

def query_progress_message(id: str, duration: float) -> str:
    return (
        query_progress_header(duration) +
        # Print with whitespace to align with the end of the transaction ID
        f"{GRAY_COLOR}ID: {id}{ENDC}"
    )

def query_complete_message(id: str, duration: float, status_header: bool = False) -> str:
    return (
        (f"{GREEN_COLOR}✅ " if status_header else "") +
        # Print with whitespace to align with the end of the transaction ID
        f"Query Complete: {format_duration(duration):>21}\n" +
        f"{GRAY_COLOR}ID: {id}{ENDC}"
    )
