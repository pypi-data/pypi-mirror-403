# language=sql
create_entities_table = """
if object_id('core.entities') is null
begin
    create table core.entities (
        [entity_id] bigint primary key identity,
        [entity_name] varchar(100) not null,
        [template] varchar(50) not null,
        [created] datetime2(7) not null default sysdatetime(),
        [updated] datetime2(7) not null default sysdatetime(),
        [is_deleted] bit not null default 0,
        [deleted] datetime2(7) default null,
        unique ([entity_name])
    );
end
"""

# language=sql
create_proc_register_entity = """
create or alter proc core.register_entity (
	@entity_name varchar(100),
	@template varchar(50)
) as
begin
	set nocount on;

	if exists (
		select *
		from core.[entities]
		where [entity_name] = @entity_name
	)
	begin
		update core.[entities]
		set [updated] = sysdatetime(), [is_deleted] = 0
		where [entity_name] = @entity_name
	end
	else begin
		insert into core.[entities]
		([entity_name], [template])
		values (@entity_name, @template)
	end
end
"""

# language=sql
create_table_ExecutionLog = """
if object_id('core.ExecutionLog') is null
begin
    create table [core].[ExecutionLog](
        [executionID] [bigint] identity(1,1) primary key NOT NULL,
        [procid] [int] NOT NULL,
        [begin_timestamp] [datetime2](7) NOT NULL default (getdate()),
        [end_timestamp] [datetime2](7) NULL default (NULL),
        [errorID] [int] NULL,
        [procname] [varchar](200) NULL,
        [parent_executionID] [bigint] NULL
    )
end
"""

# language=sql
create_table_ErrorLog = """
if object_id('core.ErrorLog') is null
begin
    create table [core].[ErrorLog](
        [ErrorID] [int] IDENTITY(1,1) NOT NULL,
        [UserName] [varchar](100) NULL,
        [ErrorNumber] [int] NULL,
        [ErrorState] [int] NULL,
        [ErrorSeverity] [int] NULL,
        [ErrorLine] [int] NULL,
        [ErrorProcedure] [varchar](max) NULL,
        [ErrorMessage] [varchar](max) NULL,
        [ErrorDateTime] [datetime] NULL
    );
end
"""

# language=sql
create_func_StringToHash = """
create or alter function [core].[StringToHash1]
(
	@StrValue1 nvarchar(1000)
) returns char(40) as
begin
	declare @result char(40);
	set @result = upper(convert(char(40), hashbytes('sha1',
		upper(rtrim(ltrim(isnull(@StrValue1, ''))))
	), 2));
	return @result;
end
"""

# language=sql
create_schemas = """
if schema_id('core') is null
    exec ('create schema core')
if schema_id('stg') is null
    exec ('create schema stg')
if schema_id('hub') is null
    exec ('create schema hub')
if schema_id('sat') is null
    exec ('create schema sat')
if schema_id('dim') is null
    exec ('create schema dim')
if schema_id('fact') is null
    exec ('create schema fact')
if schema_id('elt') is null
    exec ('create schema elt')
if schema_id('job') is null
    exec ('create schema job')
if schema_id('meta') is null
    exec ('create schema meta')
if schema_id('proxy') is null
    exec ('create schema proxy')
"""

# language=sql
create_proc_LogExecution = """
create or alter proc [core].[LogExecution]
(
	@procid int,
	@executionID_in bigint,
	@executionID_out bigint out,
	@parent_executionID bigint = null
) as
begin
	set nocount on;

	if @executionID_in is not null
	begin
		update [core].[ExecutionLog]
		set [end_timestamp] = getdate()
		where executionID = @executionID_in;

		set @executionID_out = @executionID_in;
	end else
	begin

		declare @out table (executionID int);
		insert into [core].[ExecutionLog] (procid, procname, parent_executionID) output inserted.executionID
		into @out
		values (@procid, object_name(@procid), @parent_executionID);

		set @executionID_out = (select executionID from @out);
	end
end
"""
