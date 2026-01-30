"""Dialects package for SQL code generation."""
from src.sandwich.dialects.base import DialectHandler
from src.sandwich.dialects.factory import DialectHandlerFactory
from src.sandwich.dialects.mssql import MssqlDialectHandler
from src.sandwich.dialects.postgres import PostgresDialectHandler

__all__ = [
    "DialectHandler",
    "DialectHandlerFactory",
    "MssqlDialectHandler",
    "PostgresDialectHandler",
]
