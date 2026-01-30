"""Link to Fact strategy implementations."""
from datetime import datetime
from typing import Tuple

from sqlalchemy import Table

from src.sandwich.dialects.base import DialectHandler

from .base import Validator, SchemaGenerator, ValidationResult


class Link2FactValidator(Validator):

    def validate_staging(self, stg_info: StgInfo, verbose: bool = False) -> dict:
        """Validate staging table for link2fact mode."""
        if verbose:
            raise Exception("verbose is not implemented yet")

        # TODO: Implement link2fact specific validation logic
        # This will likely be different from scd2dim validation
        # For example: checking for link keys, fact columns, etc.

        bk_keys = []
        hk_key = None
        business_column_types = {}
        system_column_types = {}
        link_keys = []  # New concept for link2fact
        fact_columns = []  # New concept for link2fact

        # Placeholder validation logic
        for col in stg_table.columns.values():
            # TODO: Implement column classification for link2fact mode
            pass

        return {
            "stg_schema": stg_table.schema,
            "entity_name": stg_table.name,
            "bk_keys": bk_keys,
            "hk_key": hk_key,
            "business_column_types": business_column_types,
            "system_column_types": system_column_types,
            "link_keys": link_keys,
            "fact_columns": fact_columns,
        }


class Link2FactSchemaGenerator(SchemaGenerator):

    def __init__(self, dialect_handler: DialectHandler, validation_result: ValidationResult):
        self.dialect_handler = dialect_handler
        self._validation_result = validation_result

    @property
    def entity_info(self) -> ValidationResult:
        return self._validation_result

    def make_tables(self) -> dict[str, Table]:
        """Create link and fact tables for link2fact mode."""
        # TODO: Implement link2fact table creation
        # This will create different table structures than scd2dim
        # For example: link table, fact table (instead of hub/sat/dim)

        entity_name = self._validation_result.entity_name

        # Placeholder - actual implementation needed
        link_table: Table | None = None
        fact_table: Table | None = None

        return {
            "link": link_table,
            "fact": fact_table,
        }

    def make_procedures(
        self,
        tables: dict[str, Table],
        entity_registration_date: datetime,
    ) -> dict[str, Tuple[str, str]]:
        """Generate procedures for link2fact mode."""
        procedures = {}

        # TODO: Implement link2fact procedure generation using dialect_handler
        # This will generate different procedures than scd2dim
        # For example: link population, fact population, aggregation logic, etc.

        # When implementing, use self.dialect_handler methods to generate SQL
        # Example:
        # link_proc_code, link_proc_name = self.dialect_handler.make_link_proc(...)
        # procedures["link"] = (link_proc_code, link_proc_name)

        return procedures