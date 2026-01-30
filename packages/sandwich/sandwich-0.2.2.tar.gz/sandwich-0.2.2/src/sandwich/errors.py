from typing import Any

class _Dv2TemplatedError(Exception):
    """Override `_template` with a string using `{value}` placeholder and optionally `{field}` placeholder.
    Example: `_template = "User with {field}={value} not found"`
    """

    _template: str

    def __init__(self, value: Any, field: str | None = None):
        template = getattr(self, "_template", None)
        if not template:
            raise NotImplementedError("_template is not implemented")

        if field:
            message = template.format(field=field, value=value)
        else:
            message = template.format(value=value)

        super().__init__(message)

class Dv2NotYetImplementedForDialectError(_Dv2TemplatedError):
    _template = "Not yet implemented for '{value}' dialect"
    def __init__(self, value: Any):
        super().__init__(value)
