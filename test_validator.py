import pytest

from validator import (
    Email,
    IntType,
    MaxLength,
    MinLength,
    Pattern,
    Range,
    Required,
    StringType,
    ValidationResult,
    Validator,
)


def test_add_rule_chaining_and_multiple_rules_per_field():
    v = Validator().add_rule("username", Required()).add_rule("username", StringType()).add_rule(
        "username", MinLength(3)
    )
    assert "username" in v.rules
    assert len(v.rules["username"]) == 3


def test_required_missing_field_fails_immediately_for_that_field_and_skips_other_rules():
    v = Validator()
    v.add_rule("x", Required())
    v.add_rule("x", StringType())
    v.add_rule("x", MinLength(2))

    result = v.validate({})
    assert not result
    assert result.errors["x"] == ["Field is required."]


def test_required_none_fails():
    v = Validator().add_rule("x", Required())
    result = v.validate({"x": None})
    assert not result.is_valid
    assert result.errors == {"x": ["Field is required."]}


def test_required_empty_string_passes_but_minlength_can_fail():
    v = Validator().add_rule("x", Required()).add_rule("x", MinLength(1))
    result = v.validate({"x": ""})
    assert not result
    assert "x" in result.errors
    assert "Length must be at least 1." in result.errors["x"][0]


def test_missing_field_without_required_is_skipped_and_passes():
    v = Validator().add_rule("age", IntType()).add_rule("age", Range(0, 150))
    result = v.validate({})
    assert result.is_valid
    assert result.errors == {}


def test_stringtype_and_inttype_type_checks():
    v = Validator().add_rule("s", StringType()).add_rule("i", IntType())
    result = v.validate({"s": 123, "i": "nope"})
    assert not result
    assert result.errors["s"] == ["Value must be a string."]
    assert result.errors["i"] == ["Value must be an integer."]


def test_minlength_and_maxlength_fail_on_non_string_with_clear_message():
    v = Validator().add_rule("x", MinLength(2)).add_rule("y", MaxLength(2))
    result = v.validate({"x": 5, "y": 10})
    assert not result
    assert result.errors["x"] == ["Value must be a string to check minimum length."]
    assert result.errors["y"] == ["Value must be a string to check maximum length."]


def test_range_fails_on_non_number_with_clear_message_and_out_of_range_fails():
    v = Validator().add_rule("x", Range(0, 10)).add_rule("y", Range(0, 10))
    result = v.validate({"x": "nope", "y": 11})
    assert not result
    assert result.errors["x"] == ["Value must be a number to check range."]
    assert result.errors["y"] == ["Value must be between 0 and 10."]


def test_pattern_uses_fullmatch_and_validates_string_type():
    v = Validator().add_rule("code", Pattern(r"[A-Z]{3}[0-9]{2}"))

    result1 = v.validate({"code": "ABC12"})
    assert result1.is_valid

    result2 = v.validate({"code": "XABC12Y"})
    assert not result2
    assert result2.errors["code"] == ["Value does not match required pattern."]

    result3 = v.validate({"code": 12345})
    assert not result3
    assert result3.errors["code"] == ["Value must be a string to match pattern."]


def test_email_rule_valid_and_invalid_and_type_check():
    v = Validator().add_rule("email", Email())

    ok = v.validate({"email": "a.b+c_1@ex-ample.com"})
    assert ok.is_valid

    bad = v.validate({"email": "invalid"})
    assert not bad
    assert bad.errors["email"] == ["Value must be a valid email address."]

    bad_type = v.validate({"email": 12})
    assert not bad_type
    assert bad_type.errors["email"] == ["Value must be a string to be a valid email."]


def test_error_aggregation_across_fields_and_rules_and_example_usage_like_behavior():
    v = Validator()
    v.add_rule("username", Required())
    v.add_rule("username", StringType())
    v.add_rule("username", MinLength(3))
    v.add_rule("username", MaxLength(20))
    v.add_rule("email", Required())
    v.add_rule("email", Email())
    v.add_rule("age", IntType())
    v.add_rule("age", Range(0, 150))

    result = v.validate({"username": "ab", "email": "invalid", "age": 200})

    assert not result.is_valid
    assert "username" in result.errors
    assert "email" in result.errors
    assert "age" in result.errors

    # Multiple rules per field should accumulate (username minlength fails).
    assert "Length must be at least 3." in result.errors["username"]
    assert result.errors["email"] == ["Value must be a valid email address."]
    assert result.errors["age"] == ["Value must be between 0 and 150."]


def test_validationresult_bool_behavior():
    vr = ValidationResult(is_valid=True, errors={})
    assert bool(vr) is True
    vr2 = ValidationResult(is_valid=False, errors={"x": ["err"]})
    assert bool(vr2) is False
