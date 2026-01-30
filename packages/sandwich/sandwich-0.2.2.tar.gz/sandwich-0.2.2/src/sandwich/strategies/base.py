from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Tuple

from sqlalchemy import Table

from src.sandwich.modeling import StgInfo

class ValidationResult:
    def __init__(self, stg_schema: str, entity_name: str
                 , bk_keys: list[Tuple[str, Any]]
                 , hk_key: Tuple[str, Any]
                 , business_column_types: dict[str, Any]
                 , system_column_types: dict[str, Any]):
        self.stg_schema = stg_schema
        self.entity_name = entity_name
        self.bk_keys = bk_keys
        self.hk_key = hk_key
        self.business_column_types = business_column_types
        self.system_column_types = system_column_types

class Validator(ABC):
    @abstractmethod
    def validate_staging(self, stg_info: StgInfo, verbose: bool = False) -> ValidationResult:
        pass


class SchemaGenerator(ABC):
    @property
    @abstractmethod
    def entity_info(self) -> ValidationResult: ...

    @abstractmethod
    def make_tables(self) -> dict[str, Table]:
        pass

    @abstractmethod
    def make_procedures(
        self,
        tables: dict[str, Table],
        entity_registration_date: datetime = datetime.now()
    ) -> dict[str, Tuple[str, str, str]]:
        pass

