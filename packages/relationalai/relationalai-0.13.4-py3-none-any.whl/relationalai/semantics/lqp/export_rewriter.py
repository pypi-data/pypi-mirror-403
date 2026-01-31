#----------------------------------------------------------------------------------------------
# This is a custom LQP rewriter that filters extra columns from CSV export. It is used in the
# LQP executor, when the format="csv", to ensure only intended columns are being exported.
#----------------------------------------------------------------------------------------------

from dataclasses import replace
from lqp import ir as lqp_ir

class ExtraColumnsFilter:

    def __init__(self, original_cols: list[str]):
        self.original_cols = set(original_cols)

    def filter_epoch(self, query_epoch: lqp_ir.Epoch) -> lqp_ir.Epoch:

        # Only process epochs with a single read which is dedicated to Export
        if not (query_epoch.reads and len(query_epoch.reads) == 1):
            return query_epoch

        old_read = query_epoch.reads[0]
        if not isinstance(old_read.read_type, lqp_ir.Export):
            return query_epoch

        config = old_read.read_type.config
        assert isinstance(config, lqp_ir.ExportCSVConfig) and config.data_columns is not None, \
            "Expected ExportCSVConfig with data_columns in the read type"

        data_columns = config.data_columns

        # Filter data_columns to only include columns in original_cols
        new_data_columns = [col for col in data_columns if col.column_name in self.original_cols]

        # Reconstruct the nested structure with filtered data_columns
        new_config = replace(old_read.read_type.config, data_columns=new_data_columns)
        new_read_type = replace(old_read.read_type, config=new_config)
        new_read = replace(old_read, read_type=new_read_type)

        # Return new epoch with updated read
        remaining_reads = list(query_epoch.reads[1:])
        return replace(query_epoch, reads=[new_read] + remaining_reads)