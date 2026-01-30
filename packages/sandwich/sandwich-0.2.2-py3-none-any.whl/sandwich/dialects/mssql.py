"""MSSQL dialect handler for SQL code generation."""
from typing import Tuple

from sqlalchemy import dialects, Table

from .base import DialectHandler
from .utils import get_columns_list

class MssqlDialectHandler(DialectHandler):
    """Dialect handler for Microsoft SQL Server."""

    def get_boolean_type(self):
        return dialects.mssql.BIT

    def get_proc_name_format(self, schema: str, operation: str, entity_name: str) -> str:
        """Get MSSQL procedure naming format."""
        return f"[{schema}].[{operation}_{entity_name}]"

    def apply_proc_template(self, proc_name: str, sql_body: str, header: str) -> str:
        """Wrap SQL body in MSSQL procedure template with error handling."""
        # language=sql
        proc_template_sql = f"""
{header}
create or alter proc {proc_name} (@parent_executionID bigint = null) as
begin
    set nocount on;

    declare @executionID bigint;
    exec core.LogExecution @@PROCID, null, @executionID out, @parent_executionID;

begin try
    {sql_body}
    exec core.LogExecution @@PROCID, @executionID, @executionID out;
end try
begin catch
    declare @err table (ErrorID int);
    declare @ErrorMessage NVARCHAR(4000);
    declare @ErrorSeverity INT;
    declare @ErrorState INT;

    set @ErrorMessage = ERROR_MESSAGE();
    set @ErrorSeverity = ERROR_SEVERITY();
    set @ErrorState = ERROR_STATE();

    insert into core.ErrorLog
    output inserted.ErrorID into @err
    values (
        SUSER_SNAME(),
        ERROR_NUMBER(),
        @ErrorState,
        @ErrorSeverity,
        ERROR_LINE(),
        ERROR_PROCEDURE(),
        @ErrorMessage,
        getdate()
    );

    update [core].[ExecutionLog]
    set [errorID] = (select ErrorID from @err)
    , [end_timestamp] = getdate()
    where [executionID] = @executionID;

    RAISERROR (
        @ErrorMessage,
        @ErrorSeverity,
        @ErrorState
    );
end catch
end
"""
        return proc_template_sql

    def make_stg_materialization_proc(self, entity_name: str, header: str) -> Tuple[str, str, str]:
        proc_name = self.get_proc_name_format("elt", f"Populate_stg", entity_name)

        # language=sql
        proc_body = f"""
    if object_id('stg.{entity_name}') is not null drop table stg.{entity_name};
    select *
    into stg.{entity_name}
    from proxy.{entity_name};
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"

    def make_hub_proc(self, hub_table: Table, bk_keys: list, header: str) -> Tuple[str, str, str]:
        proc_name = self.get_proc_name_format("elt", f"Populate_{hub_table.schema}", hub_table.name)
        where_fields_list_str = " and ".join([f"hub.[{bk[0]}] = stg.[{bk[0]}]" for bk in bk_keys])
        columns_list = get_columns_list(hub_table)

        # language=sql
        proc_body = f"""
    insert into [{hub_table.schema}].[{hub_table.name}]
    ({columns_list})
    select distinct {get_columns_list(hub_table, alias="stg")}
    from stg.[{hub_table.name}] as stg
    where not exists (
        select *
        from [{hub_table.schema}].[{hub_table.name}] as hub
        where {where_fields_list_str}
    );
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"

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
        proc_name = self.get_proc_name_format("elt", f"Populate_{sat_table.schema}", sat_table.name)
        columns_list = get_columns_list(sat_table)

        def smart_replace(column_name: str) -> str:
            if column_name == "LoadDate":
                result = "sysdatetime() as [LoadDate]"
            elif column_name == "IsAvailable":
                result = "cast(0 as bit) as [IsAvailable]"
            else:
                result = f"sat.[{column_name}]"
            return result

        select_columns_list = ", ".join([smart_replace(col.name) for col in sat_table.columns.values()])

        if stg_schema == "proxy":
            stg_table_name = f"stg.[{sat_table.name}]"
            materialization_stmt = ""
        else:
            stg_table_name = "#materialized"
            materialization_stmt = f"""
    select distinct {columns_list}
    into #materialized
    -- drop table #materialized
    from stg.[{sat_table.name}];
"""

        # language=sql
        proc_body = f"""{materialization_stmt}
    with ranked_history as
    (
        select {columns_list}
        , row_number() over (partition by [{hk_name}] order by [{loaddate_col}] desc) [DescRank]
        from [{sat_table.schema}].[{sat_table.name}]
    )
    insert into [{sat_table.schema}].[{sat_table.name}]
    ({columns_list})
    select {get_columns_list(sat_table, alias="stg")}
    from {stg_table_name} stg
    where not exists (
        select *
        from ranked_history sat
        where sat.[DescRank] = 1
        and stg.[{hk_name}] = sat.[{hk_name}]
        and stg.[{hashdiff_col}] = sat.[{hashdiff_col}]
        and sat.[{is_available_col}] = 1
    )

    union all

    select {select_columns_list}
    from ranked_history sat
    where not exists (
        select *
        from {stg_table_name} stg
        where stg.[{hk_name}] = sat.[{hk_name}]
    )
    and sat.[DescRank] = 1
    and sat.[{is_available_col}] = 1;
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"

    def make_dim_scd2_proc(
        self,
        dim_table: Table,
        bk_keys: list,
        header: str
    ) -> Tuple[str, str, str]:
        proc_name = self.get_proc_name_format("elt", f"Recalculate_{dim_table.schema}", dim_table.name)
        columns_list = get_columns_list(dim_table)
        pk_keys = lambda: ", ".join([f"sat.[{bk[0]}]" for bk in bk_keys])

        def smart_replace(column_name: str) -> str:
            if column_name == "DateFrom":
                result = "sat.LoadDate as [DateFrom]"
            elif column_name == "DateTo":
                result = f"lead(dateadd(microsecond, -1, sat.LoadDate), 1, '9999-12-31 23:59:59.9999999') over (partition by {pk_keys()} order by sat.LoadDate) [DateTo]"
            elif column_name == "IsCurrent":
                result = f"iif(lead(sat.LoadDate) over (partition by {pk_keys()} order by sat.LoadDate) is null, 1, 0) [IsCurrent]"
            else:
                result = f"sat.[{column_name}]"
            return result

        select_columns_list = "\n\t, ".join([smart_replace(col.name) for col in dim_table.columns.values()])

        # language=sql
        proc_body = f"""
    truncate table [{dim_table.schema}].[{dim_table.name}];

    insert into [{dim_table.schema}].[{dim_table.name}]
    ({columns_list})
    select {select_columns_list}
    from sat.[{dim_table.name}] sat
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"

    def make_job_proc(
        self,
        entity_name: str,
        hub_proc_name: str,
        sat_proc_name: str,
        dim_proc_name: str,
        stg_proc_name: str | None,
        header: str
    ) -> Tuple[str, str, str]:
        """Generate MSSQL job orchestration procedure."""
        proc_name = f"[job].[Run_all_related_to_{entity_name}]"

        stg_call = f"    exec {stg_proc_name} @executionID;\n" if stg_proc_name else ""

        # language=sql
        proc_body = f"""
{stg_call}    exec {hub_proc_name} @executionID;
    exec {sat_proc_name} @executionID;
    exec {dim_proc_name} @executionID;
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"

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
        """Generate MSSQL cleanup/drop procedure."""
        proc_name = f"[meta].[Drop_all_related_to_{entity_name}]"

        stg_drops = f"""
    drop table if exists [stg].[{entity_name}];
    drop procedure if exists {stg_proc_name};
""" if stg_schema == "proxy" else ""

        # language=sql
        proc_body = f"""{stg_drops}
    drop table if exists [dim].[{entity_name}];
    drop procedure if exists {dim_proc_name};
    drop table if exists [sat].[{entity_name}];
    drop procedure if exists {sat_proc_name};
    drop table if exists [hub].[{entity_name}];
    drop procedure if exists {hub_proc_name};
    drop procedure if exists {job_proc_name};

    update core.[entities]
    set [deleted] = sysdatetime()
    , [is_deleted] = 1
    where [entity_name] = '{entity_name}'
"""
        proc_code = self.apply_proc_template(proc_name, proc_body, header)
        return proc_code, proc_name, f"exec {proc_name}"
