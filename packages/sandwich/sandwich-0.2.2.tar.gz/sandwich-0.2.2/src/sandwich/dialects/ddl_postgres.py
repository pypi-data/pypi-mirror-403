# language=sql
create_extensions = """
create extension if not exists pgcrypto;
"""

# language=sql
create_entities_table = """
CREATE TABLE IF NOT EXISTS core.entities (
    entity_id BIGSERIAL PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL,
    template VARCHAR(50) NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT NOW(),
    updated TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted TIMESTAMP DEFAULT NULL,
    UNIQUE (entity_name)
);
"""

# language=sql
create_proc_register_entity = """
CREATE OR REPLACE PROCEDURE core.register_entity(
    p_entity_name VARCHAR(100),
    p_gen_path VARCHAR(50)
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO core.entities (entity_name, template)
    VALUES (p_entity_name, p_gen_path)
    ON CONFLICT (entity_name) DO UPDATE
    SET updated = NOW(),
        is_deleted = FALSE;
END;
$$;
"""

# language=sql
create_func_StringToHash= """
create or replace function core.string_to_hash1(str_value text)
returns char(40)
language plpgsql
as $$
declare
    result char(40);
begin
    if str_value is null
       or str_value in ('(unknown)', 'empty')
    then
        result := repeat('0', 40);
    else
        result :=
            upper(
                encode(
                    digest(upper(trim(str_value)), 'sha1'),
                    'hex'
                )
            );
    end if;

    return cast(result as char(40));
end;
$$;
"""

# language=sql
create_table_ExecutionLog = """
CREATE TABLE IF NOT EXISTS core.ExecutionLog (
    executionID BIGSERIAL PRIMARY KEY,
    procid INT NOT NULL,
    begin_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    end_timestamp TIMESTAMP DEFAULT NULL,
    errorID INT DEFAULT NULL,
    procname VARCHAR(200) DEFAULT NULL,
    parent_executionID BIGINT DEFAULT NULL
);
"""

# language=sql
create_table_ErrorLog = """
CREATE TABLE IF NOT EXISTS core.ErrorLog (
    ErrorID SERIAL PRIMARY KEY,
    UserName VARCHAR(100) DEFAULT NULL,
    ErrorNumber INT DEFAULT NULL,
    ErrorState INT DEFAULT NULL,
    ErrorSeverity INT DEFAULT NULL,
    ErrorLine INT DEFAULT NULL,
    ErrorProcedure TEXT DEFAULT NULL,
    ErrorMessage TEXT DEFAULT NULL,
    ErrorDateTime TIMESTAMP DEFAULT NULL
);
"""

# language=sql
create_proc_LogExecution = """
CREATE OR REPLACE PROCEDURE core.LogExecution(
    p_procid INT,
    p_executionID_in BIGINT,
    INOUT p_executionID_out BIGINT,
    p_parent_executionID BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_executionID_in IS NOT NULL THEN
        UPDATE core.ExecutionLog
        SET end_timestamp = NOW()
        WHERE executionID = p_executionID_in;

        p_executionID_out := p_executionID_in;
    ELSE
        INSERT INTO core.ExecutionLog (procid, procname, parent_executionID)
        VALUES (p_procid, NULL, p_parent_executionID)
        RETURNING executionID INTO p_executionID_out;
    END IF;
END;
$$;
"""

# language=sql
create_schemas = f"""
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS hub;
CREATE SCHEMA IF NOT EXISTS sat;
CREATE SCHEMA IF NOT EXISTS dim;
CREATE SCHEMA IF NOT EXISTS fact;
CREATE SCHEMA IF NOT EXISTS elt;
CREATE SCHEMA IF NOT EXISTS job;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS proxy;
"""