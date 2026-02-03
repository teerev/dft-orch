import re

from validator import (
    Email,
    Length,
    NumberRange,
    Pattern,
    Required,
    TypeCheck,
    Validator,
)


def test_required_missing_and_whitespace() -> None:
    v = Validator().add_check("name", Required())

    r1 = v.run({})
    assert not r1.ok
    assert "name" in r1.errors
    assert len(r1.errors["name"]) == 1
    assert r1.errors["name"][0].code == "required"

    r2 = v.run({"name": "   "})
    assert not r2.ok
    assert r2.errors["name"][0].code == "required"


def test_optional_field_skips_other_checks_if_absent() -> None:
    v = Validator().add_check("age", NumberRange(18, 120))
    r = v.run({})
    assert r.ok
    assert len(r.errors["age"]) == 0


def test_typecheck_blocks_follow_on_checks() -> None:
    v = (
        Validator()
        .add_check("age", TypeCheck(int))
        .add_check("age", NumberRange(18, 120))
    )

    r = v.run({"age": "19"})
    assert not r.ok
    assert len(r.errors["age"]) == 1
    assert r.errors["age"][0].code == "type"


def test_number_range_accepts_int_and_float() -> None:
    v = Validator().add_check("price", NumberRange(0.0, 10.5))
    assert v.run({"price": 0}).ok
    assert v.run({"price": 10.5}).ok

    r = v.run({"price": 11.0})
    assert not r.ok
    assert r.errors["price"][0].code == "range"


def test_length_text_only_and_bounds() -> None:
    v = Validator().add_check("username", Length(min_len=3, max_len=8))

    assert not v.run({"username": "ab"}).ok
    assert v.run({"username": "abcd"}).ok
    assert not v.run({"username": "abcdefghi"}).ok

    r = v.run({"username": 123})
    assert not r.ok
    assert r.errors["username"][0].code == "type"


def test_email_validation_basic() -> None:
    v = Validator().add_check("email", Email())

    assert v.run({"email": "a@b.co"}).ok

    r = v.run({"email": "not-an-email"})
    assert not r.ok
    assert r.errors["email"][0].code == "email"


def test_pattern_fullmatch_and_type_error() -> None:
    v = Validator().add_check("zip", Pattern(r"\d{5}"))

    assert v.run({"zip": "12345"}).ok

    r1 = v.run({"zip": "1234a"})
    assert not r1.ok
    assert r1.errors["zip"][0].code == "pattern"

    r2 = v.run({"zip": 12345})
    assert not r2.ok
    assert r2.errors["zip"][0].code == "type"


def test_aggregates_multiple_fields_and_chainable_add_check() -> None:
    v = (
        Validator()
        .add_check("email", Required())
        .add_check("email", Email())
        .add_check("age", Required())
        .add_check("age", TypeCheck(int))
        .add_check("age", NumberRange(18, 120))
        .add_check("username", Length(min_len=3))
        .add_check("code", Pattern(re.compile(r"[A-Z]{2}\d{2}")))
    )

    r = v.run({"email": "bad", "age": "old", "username": "a", "code": "zz99"})
    assert not r.ok

    assert r.errors["email"][0].code == "email"
    assert r.errors["age"][0].code == "type"  # type check blocks range
    assert r.errors["username"][0].code == "length"
    assert r.errors["code"][0].code == "pattern"
