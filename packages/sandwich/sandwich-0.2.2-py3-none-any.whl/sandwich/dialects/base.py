from abc import ABC, abstractmethod
from typing import Tuple

from sqlalchemy import Table

class DialectHandler(ABC):
    @abstractmethod
    def get_boolean_type(self): ...

    @abstractmethod
    def get_proc_name_format(self, schema: str, operation: str, entity_name: str) -> str:
        pass

    @abstractmethod
    def apply_proc_template(self, proc_name: str, sql_body: str, header: str) -> str:
        """Wrap SQL body in procedure template with error handling and logging.

        Args:
            proc_name: Name of the procedure
            sql_body: The main SQL logic to execute
            header: Auto-generated header comment

        Returns:
            Complete procedure definition
        """
        pass

    @abstractmethod
    def make_stg_materialization_proc(
        self,
        entity_name: str,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate staging table materialization procedure.

        Args:
            entity_name: Entity name
            columns_list: Comma-separated list of columns
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass

    @abstractmethod
    def make_hub_proc(
        self,
        hub_table: Table,
        bk_keys: list,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate hub population procedure.

        Args:
            hub_table: SQLAlchemy Table object for hub
            bk_keys: List of business key tuples (name, type)
            columns_list: Comma-separated list of columns
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass

    @abstractmethod
    def make_sat_proc(
        self,
        sat_table: Table,
        hk_name: str,
        hashdiff_col: str,
        is_available_col: str,
        loaddate_col: str,
        stg_schema: str,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate satellite population procedure.

        Args:
            sat_table: SQLAlchemy Table object for satellite
            hk_name: Hash key column name
            hashdiff_col: Hash diff column name
            is_available_col: Is available column name
            loaddate_col: Load date column name
            columns_list: Comma-separated list of columns
            stg_schema: Staging schema name ('stg' or 'proxy')
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass

    @abstractmethod
    def make_dim_scd2_proc(
        self,
        dim_table: Table,
        bk_keys: list,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate dimension SCD2 recalculation procedure.

        Args:
            dim_table: SQLAlchemy Table object for dimension
            bk_keys: List of business key tuples (name, type)
            columns_list: Comma-separated list of columns
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass

    @abstractmethod
    def make_job_proc(
        self,
        entity_name: str,
        hub_proc_name: str,
        sat_proc_name: str,
        dim_proc_name: str,
        stg_proc_name: str | None,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate main job orchestration procedure.

        Args:
            entity_name: Entity name
            hub_proc_name: Name of hub population procedure
            sat_proc_name: Name of satellite population procedure
            dim_proc_name: Name of dimension recalculation procedure
            stg_proc_name: Name of staging materialization procedure (optional)
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass

    @abstractmethod
    def make_drop_proc(
        self,
        entity_name: str,
        stg_schema: str,
        job_proc_name: str,
        stg_proc_name: str | None,
        hub_proc_name: str,
        sat_proc_name: str,
        dim_proc_name: str,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate cleanup/drop procedure for all entity objects.

        Args:
            entity_name: Entity name
            stg_schema: Staging schema name ('stg' or 'proxy')
            job_proc_name: Name of job orchestration procedure
            stg_proc_name: Name of staging materialization procedure (optional)
            hub_proc_name: Name of hub population procedure
            sat_proc_name: Name of satellite population procedure
            dim_proc_name: Name of dimension recalculation procedure
            header: Auto-generated header comment

        Returns:
            Tuple of (procedure_code, procedure_name)
        """
        pass
