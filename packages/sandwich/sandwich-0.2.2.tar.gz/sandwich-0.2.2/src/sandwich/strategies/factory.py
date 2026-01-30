from src.sandwich.dialects import DialectHandler

from .base import Validator, SchemaGenerator, ValidationResult
from .link2fact import Link2FactValidator, Link2FactSchemaGenerator
from .scd2dim import Scd2DimValidator, Scd2DimSchemaGenerator


class StrategyFactory:
    _strategies = {
        "scd2dim": (Scd2DimValidator, Scd2DimSchemaGenerator),
        "link2fact": (Link2FactValidator, Link2FactSchemaGenerator),
    }

    @classmethod
    def register_strategy(cls, template_name: str, validator_class, generator_class):
        cls._strategies[template_name] = (validator_class, generator_class)

    @classmethod
    def create_validator(cls, template: str) -> Validator:
        if template not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown template '{template}'. Available templates: {available}")

        validator_class, _ = cls._strategies[template]
        return validator_class()

    @classmethod
    def create_generator(cls, template: str, dialect_handler: DialectHandler, validation_result: ValidationResult) -> SchemaGenerator:
        if template not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown template '{template}'. Available templates: {available}")

        _, generator_class = cls._strategies[template]
        return generator_class(dialect_handler, validation_result)

    @classmethod
    def get_available_templates(cls) -> list[str]:
        return list(cls._strategies.keys())
