from datetime import datetime

from sqlalchemy import Connection, Engine, MetaData, Table, select, text

from src.sandwich.dialects import DialectHandlerFactory
from src.sandwich.modeling import get_stg_info, infer_template
from src.sandwich.strategies import StrategyFactory

from . import errors as err


class Dv2Helper:

    def __init__(self, stg: Table, dialect: str = "mssql", template: str | None = None):
        stg_info = get_stg_info(stg)
        if template is None:
            template = infer_template(stg_info)
        if template not in ("scd2dim", "link2fact"):
            raise ValueError(
                f"Template '{template}' is not supported. Supported templates: scd2dim, link2fact"
            )

        # legacy fields
        self.stg_table = stg
        self.entity_name = stg.name
        self.template = template

        self.dialect = dialect
        self.dialect_handler = DialectHandlerFactory.create_handler(dialect)
        self.validator = StrategyFactory.create_validator(template)
        self.validation_result = self.validator.validate_staging(stg_info)
        self.schema_generator = StrategyFactory.create_generator(template,
                                                                 self.dialect_handler,
                                                                 self.validation_result)

        # Convenience properties (for backward compatibility if needed)
        self.bk_keys = self.validation_result.bk_keys
        self.hk_key = self.validation_result.hk_key
        self.business_column_types = self.validation_result.business_column_types
        self.system_column_types = self.validation_result.system_column_types

    def call_register_entity(self, conn: Engine | Connection) -> datetime:
        if self.dialect == "mssql":
            call_stmt = "exec core.[register_entity] :entity_name, :template"
        elif self.dialect == "postgres":
            call_stmt = "call core.register_entity (:entity_name, :template)"
        else:
            raise err.Dv2NotYetImplementedForDialectError(self.dialect)

        conn.execute(
            text(call_stmt),
            {
                "entity_name": self.entity_name,
                "template": self.template,
            })

        entities = Table("entities", MetaData(), schema="core", autoload_with=conn)
        stmt = select(entities.c.created).where(self.entity_name == entities.c.entity_name)
        return conn.execute(stmt).scalar_one()

    # def call_job_proc(self, conn: Engine | Connection, parent_execution_id: int = -1) -> None:
    #     job_proc_name = self.schema_generator.get_job_proc_name(self.entity_name, self.dialect)
    #
    #     if self.dialect == "mssql":
    #         call_stmt = f"exec {job_proc_name} :parent_executionID"
    #     else:
    #         raise err.Dv2NotYetImplementedForDialectError(self.dialect)
    #
    #     conn.execute(text(call_stmt), {"parent_executionID": parent_execution_id})

    def generate_schema(self, conn: Engine | Connection, verbose: bool = False) -> None:
        registered_on = self.call_register_entity(conn)
        if verbose:
            print(f"[ok] Registered `{self.entity_name}` for `{self.template}`")

        tables = self.schema_generator.make_tables()
        for table_type, table in tables.items():
            if table is not None:
                table.create(conn, checkfirst=True)
                if verbose:
                    print(f"[ok] Created table [{table.schema}].[{table.name}]")

        procedures = self.schema_generator.make_procedures(tables, registered_on)
        for proc_type, (proc_code, proc_name, _) in procedures.items():
            conn.execute(text(proc_code))
            if verbose:
                print(f"[ok] Created or altered {proc_name}")

    @classmethod
    def update_registered_entities(cls, conn: Engine | Connection, dialect: str = "mssql",
                                   verbose: bool = False):
        metadata = MetaData()
        entities = Table("entities", metadata, schema="core", autoload_with=conn)
        select_result = conn.execute(entities.select().where(~entities.c.is_deleted))
        for row in select_result.mappings().all():
            stg = Table(row["entity_name"], metadata, schema="stg", autoload_with=conn)
            dv2 = cls(stg, dialect=dialect, template=row["template"])
            dv2.generate_schema(conn, verbose=verbose)