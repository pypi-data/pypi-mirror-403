from datetime import datetime
from typing import Iterator, Tuple

from sqlalchemy import Column, MetaData, Table, UniqueConstraint

from src.sandwich import SANDWICH_VERSION
from src.sandwich.dialects.base import DialectHandler
from src.sandwich.modeling import modeling_metadata, StgInfo

from .base import Validator, SchemaGenerator, ValidationResult


class Scd2DimValidator(Validator):

    def validate_staging(self, stg_info: StgInfo, verbose: bool = False) -> ValidationResult:
        """Validate staging table or view for `scd2dim` template.

        Raises: Exception"""
        if verbose:
            raise Exception("verbose is not implemented yet")

        # -----------------
        # hk
        # -----------------
        # only one hash key is allowed for `scd2dim` profile
        # and its name should match `hk_[entity_name]` pattern
        hk_count = len(stg_info.hk_keys)
        if hk_count == 0:
            raise Exception("hk column is required for `scd2dim` validation")
        elif hk_count > 1:
            raise Exception(f"More than one hk column found in stg.{stg_info.stg_name}")
        # hk_key = (key_name, key_type)
        hk_key = list(stg_info.hk_keys.items())[0]
        if hk_key[0] != f"hk_{stg_info.stg_name}":
            raise Exception(f"hk column has invalid name '{hk_key[0]}'")

        # -----------------
        # BKs
        # -----------------
        # You don't need a hub or/and a dim tables for a non-business entity.
        # So you have to have at least one business key, and you can have more.
        # Naming convention is to just add a `bk_` prefix to the original key name
        # because we want to keep information of the original names
        if len(stg_info.bk_keys) == 0:
            raise Exception("bk column(s) are required for `scd2dim` validation")


        system_column_names = stg_info.sys_columns.keys()

        # universal check - all dv2 raw objects should be auditable
        for required_col in modeling_metadata.required_columns:
            if required_col not in system_column_names:
                raise Exception(f"{required_col} column is required")

        # scd2dim specific validations
        if modeling_metadata.hashdiff not in system_column_names:
            raise Exception(f"{modeling_metadata.hashdiff} column is required for scd2dim validation")
        if modeling_metadata.is_available not in system_column_names:
            raise Exception(f"{modeling_metadata.is_available} column is required for scd2dim validation")

        return ValidationResult(
            stg_schema=stg_info.stg_schema,
            entity_name=stg_info.stg_name,
            bk_keys=[(nm, tp) for nm, tp in stg_info.bk_keys.items()],
            hk_key=hk_key,
            business_column_types=stg_info.bus_columns,
            system_column_types=stg_info.sys_columns,
        )

class Scd2DimSchemaGenerator(SchemaGenerator):

    def __init__(self, dialect_handler: DialectHandler, validation_result: ValidationResult):
        self.dialect_handler = dialect_handler
        self._validation_result = validation_result

    @property
    def entity_info(self) -> ValidationResult:
        return self._validation_result

    def make_tables(self) -> dict[str, Table]:
        entity_name = self._validation_result.entity_name
        bk_keys = self._validation_result.bk_keys
        hk_key = self._validation_result.hk_key
        business_column_types = self._validation_result.business_column_types
        system_column_types = self._validation_result.system_column_types

        # Helper functions for creating columns
        def get_bk_columns() -> Iterator[Column]:
            return (Column(bk_key[0], bk_key[1], nullable=False) for bk_key in bk_keys)

        def get_bk_pk_columns() -> Iterator[Column]:
            return (Column(bk_key[0], bk_key[1], primary_key=True) for bk_key in bk_keys)

        def get_hk_pk_column() -> Column:
            return Column(hk_key[0], hk_key[1], primary_key=True)

        def get_loaddate_column() -> Column:
            _load_date = modeling_metadata.loaddate
            _load_date_type = system_column_types[_load_date]
            return Column(_load_date, _load_date_type, nullable=False)

        def get_loaddate_pk_column() -> Column:
            _load_date = modeling_metadata.loaddate
            _load_date_type = system_column_types[_load_date]
            return Column(_load_date, _load_date_type, primary_key=True)

        def get_datefrom_pk_column() -> Column:
            _load_date = modeling_metadata.loaddate
            _load_date_type = system_column_types[_load_date]
            return Column("DateFrom", _load_date_type, primary_key=True)

        def get_dateto_column() -> Column:
            _load_date = modeling_metadata.loaddate
            _load_date_type = system_column_types[_load_date]
            return Column("DateTo", _load_date_type, nullable=True)

        def get_recordsource_column() -> Column:
            _record_source = modeling_metadata.recordsource
            _record_source_type = system_column_types[_record_source]
            return Column(_record_source, _record_source_type, nullable=False)

        def get_business_columns() -> Iterator[Column]:
            return (Column(col_name, col_type, nullable=True) for (col_name, col_type) in business_column_types.items())

        def get_is_available_column() -> Column:
            _is_available = modeling_metadata.is_available
            _is_available_type = system_column_types[_is_available]
            return Column(_is_available, _is_available_type, nullable=False)

        def get_hashdiff_column() -> Column:
            _hashdiff = modeling_metadata.hashdiff
            _hashdiff_type = system_column_types[_hashdiff]
            return Column(_hashdiff, _hashdiff_type, nullable=False)

        # Create hub table
        hub_table = Table(entity_name, MetaData(), schema="hub")
        for bk_col in get_bk_columns():
            hub_table.append_column(bk_col)
        hub_table.append_column(get_hk_pk_column())
        hub_table.append_column(get_loaddate_column())
        hub_table.append_column(get_recordsource_column())
        hub_table.append_constraint(UniqueConstraint(*[bk[0] for bk in bk_keys]))

        # Create sat table
        sat_table = Table(entity_name, MetaData(), schema="sat")
        for bk_col in get_bk_columns():
            sat_table.append_column(bk_col)
        sat_table.append_column(get_hk_pk_column())
        sat_table.append_column(get_loaddate_pk_column())
        sat_table.append_column(get_recordsource_column())
        sat_table.append_column(get_hashdiff_column())
        for business_col in get_business_columns():
            sat_table.append_column(business_col)
        sat_table.append_column(get_is_available_column())

        # Create dim table
        dim_table = Table(entity_name, MetaData(), schema="dim")
        for bk_col in get_bk_pk_columns():
            dim_table.append_column(bk_col)
        for business_col in get_business_columns():
            dim_table.append_column(business_col)
        dim_table.append_column(get_is_available_column())
        dim_table.append_column(Column("IsCurrent", self.dialect_handler.get_boolean_type(), nullable=False))
        dim_table.append_column(get_datefrom_pk_column())
        dim_table.append_column(get_dateto_column())

        return {
            "hub": hub_table,
            "sat": sat_table,
            "dim": dim_table,
        }

    def make_procedures(self, tables: dict[str, Table]
                        , entity_registration_date: datetime = datetime.now()) -> dict[str, Tuple[str, str, str]]:
        procedures = {}

        header = modeling_metadata.HEADER_TEMPLATE.format(
            created_on=entity_registration_date,
            updated_on=datetime.now(),
            version=SANDWICH_VERSION,
            entity_name=self._validation_result.entity_name
        )

        stg_proc_name = None
        if self._validation_result.stg_schema == "proxy":
            stg_proc_code, stg_proc_name, stg_call_stmt = self.dialect_handler.make_stg_materialization_proc(
                entity_name=self._validation_result.entity_name,
                header=header
            )
            procedures["stg"] = (stg_proc_code, stg_proc_name, stg_call_stmt)

        hub_table = tables["hub"]
        hub_proc_code, hub_proc_name, hub_call_stmt = self.dialect_handler.make_hub_proc(
            hub_table=hub_table,
            bk_keys=self._validation_result.bk_keys,
            header=header
        )
        procedures["hub"] = (hub_proc_code, hub_proc_name, hub_call_stmt)

        # Generate sat procedure
        sat_table = tables["sat"]
        sat_proc_code, sat_proc_name, sat_call_stmt = self.dialect_handler.make_sat_proc(
            sat_table=sat_table,
            hk_name=self._validation_result.hk_key[0],
            hashdiff_col=modeling_metadata.hashdiff,
            is_available_col=modeling_metadata.is_available,
            loaddate_col=modeling_metadata.loaddate,
            stg_schema=self._validation_result.stg_schema,
            header=header
        )
        procedures["sat"] = (sat_proc_code, sat_proc_name, sat_call_stmt)

        # Generate dim procedure
        dim_table = tables["dim"]
        dim_proc_code, dim_proc_name, dim_call_stmt = self.dialect_handler.make_dim_scd2_proc(
            dim_table=dim_table,
            bk_keys=self._validation_result.bk_keys,
            header=header
        )
        procedures["dim"] = (dim_proc_code, dim_proc_name, dim_call_stmt)

        # Generate job procedure
        job_proc_code, job_proc_name, job_call_stmt = self.dialect_handler.make_job_proc(
            entity_name=self._validation_result.entity_name,
            hub_proc_name=hub_proc_name,
            sat_proc_name=sat_proc_name,
            dim_proc_name=dim_proc_name,
            stg_proc_name=stg_proc_name,
            header=header
        )
        procedures["job"] = (job_proc_code, job_proc_name, job_call_stmt)

        # Generate drop procedure
        drop_proc_code, drop_proc_name, drop_call_stmt = self.dialect_handler.make_drop_proc(
            entity_name=self._validation_result.entity_name,
            stg_schema=self._validation_result.stg_schema,
            job_proc_name=job_proc_name,
            stg_proc_name=stg_proc_name,
            hub_proc_name=hub_proc_name,
            sat_proc_name=sat_proc_name,
            dim_proc_name=dim_proc_name,
            header=header
        )
        procedures["drop"] = (drop_proc_code, drop_proc_name, drop_call_stmt)

        return procedures
