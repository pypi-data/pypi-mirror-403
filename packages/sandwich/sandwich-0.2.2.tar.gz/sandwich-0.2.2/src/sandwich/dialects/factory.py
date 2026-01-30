from src.sandwich.dialects.base import DialectHandler
from src.sandwich.dialects.mssql import MssqlDialectHandler
from src.sandwich.dialects.postgres import PostgresDialectHandler


class DialectHandlerFactory:
    _handlers = {
        "mssql": MssqlDialectHandler,
        "postgres": PostgresDialectHandler,
    }

    @classmethod
    def register_dialect(cls, dialect_name: str, handler_class):
        cls._handlers[dialect_name] = handler_class

    @classmethod
    def create_handler(cls, dialect: str) -> DialectHandler:
        if dialect not in cls._handlers:
            available = ", ".join(cls._handlers.keys())
            raise ValueError(f"Unknown dialect '{dialect}'. Available dialects: {available}")

        handler_class = cls._handlers[dialect]
        return handler_class()

    @classmethod
    def get_available_dialects(cls) -> list[str]:
        return list(cls._handlers.keys())
