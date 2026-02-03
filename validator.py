from __future__ import annotations

import re
from typing import Any


class ValidationResult:
    def __init__(self, is_valid: bool, errors: dict[str, list[str]]):
        self.is_valid = is_valid
        self.errors = errors

    def __bool__(self) -> bool:
        return self.is_valid


class ValidationRule:
    """Base class for validation rules."""

    def check(self, value: Any) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        raise NotImplementedError


class Required(ValidationRule):
    """Field must be present and not None."""

    def check(self, value: Any) -> tuple[bool, str]:
        if value is None:
            return False, "Field is required."
        return True, ""


class StringType(ValidationRule):
    """Value must be a string."""

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string."
        return True, ""


class IntType(ValidationRule):
    """Value must be an integer."""

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, int) or isinstance(value, bool):
            return False, "Value must be an integer."
        return True, ""


class MinLength(ValidationRule):
    """String must have minimum length."""

    def __init__(self, min_len: int):
        self.min_len = min_len

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string to check minimum length."
        if len(value) < self.min_len:
            return False, f"Length must be at least {self.min_len}."
        return True, ""


class MaxLength(ValidationRule):
    """String must not exceed maximum length."""

    def __init__(self, max_len: int):
        self.max_len = max_len

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string to check maximum length."
        if len(value) > self.max_len:
            return False, f"Length must be at most {self.max_len}."
        return True, ""


class Range(ValidationRule):
    """Number must be within range (inclusive)."""

    def __init__(self, min_val: int, max_val: int):
        self.min_val = min_val
        self.max_val = max_val

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, "Value must be a number to check range."
        if value < self.min_val or value > self.max_val:
            return False, f"Value must be between {self.min_val} and {self.max_val}."
        return True, ""


class Pattern(ValidationRule):
    """String must match regex pattern."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self._compiled = re.compile(pattern)

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string to match pattern."
        if re.fullmatch(self._compiled, value) is None:
            return False, "Value does not match required pattern."
        return True, ""


class Email(ValidationRule):
    """Value must be a valid email format."""

    _EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    def __init__(self):
        self._compiled = re.compile(self._EMAIL_PATTERN)

    def check(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string to be a valid email."
        if re.fullmatch(self._compiled, value) is None:
            return False, "Value must be a valid email address."
        return True, ""


class Validator:
    def __init__(self):
        self.rules: dict[str, list[ValidationRule]] = {}

    def add_rule(self, field: str, rule: ValidationRule) -> "Validator":
        """Add a validation rule for a field. Returns self for chaining."""
        self.rules.setdefault(field, []).append(rule)
        return self

    def validate(self, data: dict) -> ValidationResult:
        """Validate data against all rules. Returns ValidationResult."""
        errors: dict[str, list[str]] = {}

        for field, rules in self.rules.items():
            has_required = any(isinstance(r, Required) for r in rules)
            is_present = field in data

            if not is_present and not has_required:
                continue

            value = data.get(field, None)

            field_errors: list[str] = []

            # If Required() exists, it fails immediately for this field when missing/None.
            if has_required:
                req_rules = [r for r in rules if isinstance(r, Required)]
                for r in req_rules:
                    ok, msg = r.check(value)
                    if not ok:
                        field_errors.append(msg)
                if field_errors:
                    errors[field] = field_errors
                    continue

            # If the field is missing and it's not required, skip.
            if not is_present:
                continue

            for rule in rules:
                if isinstance(rule, Required):
                    continue
                ok, msg = rule.check(value)
                if not ok:
                    field_errors.append(msg)

            if field_errors:
                errors[field] = field_errors

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors)
