from datetime import datetime
from typing import Any

from sqlalchemy import Engine, Connection, Table, text, TextClause

from src.sandwich import SANDWICH_VERSION
from .. import errors as err
from src.sandwich.modeling import modeling_metadata

from . import ddl_mssql, ddl_postgres

def get_columns_list(table: Table, sep: str = ", ", alias: str = None):
    alias = alias + "." if alias else ""
    return sep.join([f"{alias or ''}[{fld.name}]" for fld in table.columns.values()])

def get_string_to_hash_ddl_mssql(columns_count: int) -> str:
    if columns_count < 2 or columns_count > 100:
        raise ValueError("columns_count must be between 2 and 100")

    params_list_str = ",\n\t".join([f"@StrValue{v} nvarchar(1000)" for v in range(1, columns_count + 1)])
    concat_list_str = ", ';',\n\t\t\t".join(
        [f"rtrim(ltrim(isnull(@StrValue{v}, '')))" for v in range(1, columns_count + 1)])

    # language=sql
    func = f"""
create or alter function [core].[StringToHash{columns_count}]
(
{params_list_str}
) returns char(40) as
begin
declare @result char(40);
set @result = upper(convert(char(40), hashbytes('sha1',
    upper(concat(
        {concat_list_str}
    ))
), 2));
return @result;
end"""
    return func

def get_string_to_hash_ddl_postgres(columns_count: int) -> str:
    if columns_count < 2 or columns_count > 100:
        raise ValueError("columns_count must be between 2 and 100")

    params_list_str = ",\n\t".join([f"p_str_value{v} text" for v in range(1, columns_count + 1)])
    concat_list_str = ", ';',\n\t\t\t".join(
        [f"upper(trim(coalesce(p_str_value{v}, '')))" for v in range(1, columns_count + 1)])

    # language=sql
    func = f"""
create or replace function core.string_to_hash{columns_count}(
{params_list_str}
) returns char(40)
language plpgsql
as $$
declare
result char(40);
begin
result :=
    upper(
        encode(
            digest(
                concat(
                    {concat_list_str}
                ),
                'sha1'
            ),
            'hex'
        )
    );
return cast(result as char(40));
end;
$$;"""
    return func

def initialize_database(conn: Engine | Connection, dialect: str = "mssql",
                        str_to_hash_count:int = 66,
                        verbose: bool = False,
                        drop_entities_table: bool = False) -> None:
    init_scripts: dict[str, str] = {}
    header = modeling_metadata.HEADER_TEMPLATE.format(
        created_on=datetime.now(),
        updated_on=datetime.now(),
        version=SANDWICH_VERSION,
        entity_name="SYSTEM")

    if dialect == "mssql":
        init_scripts["create_schemas"] = ddl_mssql.create_schemas
        if drop_entities_table:
            init_scripts["drop_entities_table"] = "drop table if exists [core].[entities];"
        init_scripts["create_entities_table"] = ddl_mssql.create_entities_table
        init_scripts["create_proc_register_entity"] = header + ddl_mssql.create_proc_register_entity
        init_scripts["create_func_StringToHash1"] = header + ddl_mssql.create_func_StringToHash
        for i in range(2, str_to_hash_count):
            init_scripts[f"create_func_StringToHash{i}"] = header + get_string_to_hash_ddl_mssql(i)
        init_scripts["create_table_ExecutionLog"] = ddl_mssql.create_table_ExecutionLog
        init_scripts["create_table_ErrorLog"] = ddl_mssql.create_table_ErrorLog
        init_scripts["create_proc_LogExecution"] = header + ddl_mssql.create_proc_LogExecution
    elif dialect == "postgres":
        init_scripts["create_extensions"] = ddl_postgres.create_extensions
        init_scripts["create_schemas"] = ddl_postgres.create_schemas
        if drop_entities_table:
            init_scripts["drop_entities_table"] = "drop table if exists core.entities"
        init_scripts["create_entities_table"] = ddl_postgres.create_entities_table
        init_scripts["create_proc_register_entity"] = ddl_postgres.create_proc_register_entity
        init_scripts["create_func_StringToHash1"] = ddl_postgres.create_func_StringToHash
        for i in range(2, str_to_hash_count):
            init_scripts[f"create_func_StringToHash{i}"] = get_string_to_hash_ddl_postgres(i)
        init_scripts["create_table_ExecutionLog"] = ddl_postgres.create_table_ExecutionLog
        init_scripts["create_table_ErrorLog"] = ddl_postgres.create_table_ErrorLog
        init_scripts["create_proc_LogExecution"] = ddl_postgres.create_proc_LogExecution
    else:
        raise err.Dv2NotYetImplementedForDialectError(dialect)

    for name, script in init_scripts.items():
        if verbose:
            print(f"[ok] Executing script: {name}")
        conn.execute(text(script))

def get_proc_definition_dml_mssql(proc_param_name: str) -> TextClause:
    return text(f"""
       SELECT sm.definition
       FROM sys.sql_modules sm
                JOIN sys.objects o ON sm.object_id = o.object_id
                JOIN sys.schemas s ON o.schema_id = s.schema_id
       WHERE o.type = 'P'
         AND '['+s.name+'].['+o.name+']' = :{proc_param_name}
       """)

def parse_auto_generated_header(full_proc_text: str) -> dict[str, Any]:
    started = False
    rows_in_header = 0
    result: dict[str, Any] = {}
    for ln in full_proc_text.splitlines():
        if started:
            rows_in_header += 1
            if ln.lstrip().startswith("Created on"):
                result["created_on"] = ln.split(":", 1)[1].strip()
            elif ln.lstrip().startswith("Updated on"):
                result["updated_on"] = ln.split(":", 1)[1].strip()
            elif ln.strip() == "*/":
                break
            else:
                continue
        if ln.strip() == "/*":
            started = True
            continue
    result["rows_in_header"] = rows_in_header - 1 if rows_in_header > 0 else 0
    return result