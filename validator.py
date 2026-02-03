from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, MutableMapping, Sequence, Type


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str
    code: str


@dataclass(frozen=True)
class ValidationResult:
    errors: Mapping[str, Sequence[ValidationError]]

    @property
    def ok(self) -> bool:
        return all(len(errs) == 0 for errs in self.errors.values())


class Check:
    """Base class for all field checks."""

    code: str = "check_failed"

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        raise NotImplementedError


_MISSING = object()


def _is_absent(value: Any) -> bool:
    """True when a non-required field should skip further checks."""
    if value is _MISSING or value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


class Required(Check):
    code = "required"

    def __init__(self, message: str | None = None) -> None:
        self._message = message or "This field is required."

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if value is _MISSING or value is None:
            return [ValidationError(field=field, message=self._message, code=self.code)]
        if isinstance(value, str) and value.strip() == "":
            return [ValidationError(field=field, message=self._message, code=self.code)]
        return []


class TypeCheck(Check):
    code = "type"

    def __init__(self, expected_type: Type[Any], message: str | None = None) -> None:
        self.expected_type = expected_type
        self._message = message or f"Must be of type {expected_type.__name__}."

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if not isinstance(value, self.expected_type):
            return [ValidationError(field=field, message=self._message, code=self.code)]
        return []


class Email(Check):
    code = "email"

    # Not RFC-complete; catches obvious invalid emails.
    _EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def __init__(self, message: str | None = None) -> None:
        self._message = message or "Must be a valid email address."

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if not isinstance(value, str):
            return [ValidationError(field=field, message="Must be text.", code="type")]
        if not self._EMAIL_RE.match(value.strip()):
            return [ValidationError(field=field, message=self._message, code=self.code)]
        return []


class Length(Check):
    code = "length"

    def __init__(
        self,
        min_len: int | None = None,
        max_len: int | None = None,
        message: str | None = None,
    ) -> None:
        if min_len is None and max_len is None:
            raise ValueError("Length requires min_len and/or max_len")
        if min_len is not None and min_len < 0:
            raise ValueError("min_len must be >= 0")
        if max_len is not None and max_len < 0:
            raise ValueError("max_len must be >= 0")
        if min_len is not None and max_len is not None and min_len > max_len:
            raise ValueError("min_len must be <= max_len")

        self.min_len = min_len
        self.max_len = max_len
        self._message = message

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if not isinstance(value, str):
            return [ValidationError(field=field, message="Must be text.", code="type")]
        n = len(value)
        if self.min_len is not None and n < self.min_len:
            msg = self._message or f"Must be at least {self.min_len} characters long."
            return [ValidationError(field=field, message=msg, code=self.code)]
        if self.max_len is not None and n > self.max_len:
            msg = self._message or f"Must be at most {self.max_len} characters long."
            return [ValidationError(field=field, message=msg, code=self.code)]
        return []


class NumberRange(Check):
    code = "range"

    def __init__(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
        message: str | None = None,
    ) -> None:
        if min_value is None and max_value is None:
            raise ValueError("NumberRange requires min_value and/or max_value")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value must be <= max_value")

        self.min_value = min_value
        self.max_value = max_value
        self._message = message

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return [ValidationError(field=field, message="Must be a number.", code="type")]
        x = float(value)
        if self.min_value is not None and x < self.min_value:
            msg = self._message or f"Must be >= {self.min_value}."
            return [ValidationError(field=field, message=msg, code=self.code)]
        if self.max_value is not None and x > self.max_value:
            msg = self._message or f"Must be <= {self.max_value}."
            return [ValidationError(field=field, message=msg, code=self.code)]
        return []


class Pattern(Check):
    code = "pattern"

    def __init__(self, pattern: str | re.Pattern[str], message: str | None = None) -> None:
        self.regex: re.Pattern[str] = re.compile(pattern) if isinstance(pattern, str) else pattern
        self._message = message or "Invalid format."

    def validate(self, field: str, value: Any) -> list[ValidationError]:
        if not isinstance(value, str):
            return [ValidationError(field=field, message="Must be text.", code="type")]
        if self.regex.fullmatch(value) is None:
            return [ValidationError(field=field, message=self._message, code=self.code)]
        return []


class Validator:
    """Collects checks per field and runs them, returning all errors at once."""

    def __init__(self) -> None:
        self._checks: dict[str, list[Check]] = {}

    def add_check(self, field: str, check: Check) -> "Validator":
        self._checks.setdefault(field, []).append(check)
        return self

    def run(self, data: Mapping[str, Any]) -> ValidationResult:
        errors: MutableMapping[str, list[ValidationError]] = {}

        for field, checks in self._checks.items():
            value: Any = data.get(field, _MISSING)

            field_errors: list[ValidationError] = []
            required_present = any(isinstance(c, Required) for c in checks)

            for check in checks:
                if (not required_present) and (not isinstance(check, Required)) and _is_absent(value):
                    continue

                # If a previous type check failed, don't run other checks.
                if any(err.code == "type" for err in field_errors) and not isinstance(check, TypeCheck):
                    continue

                try:
                    field_errors.extend(check.validate(field, value))
                except Exception:
                    field_errors.append(
                        ValidationError(field=field, message="Invalid value.", code="invalid")
                    )

            errors[field] = field_errors

        return ValidationResult(errors=errors)
