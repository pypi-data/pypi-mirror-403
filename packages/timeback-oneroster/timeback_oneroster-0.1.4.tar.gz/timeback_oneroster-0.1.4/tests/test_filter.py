"""Tests for where_to_filter conversion function."""

from datetime import date, datetime

from timeback_oneroster import where_to_filter


class TestWhereToFilterSimple:
    """Tests for simple equality conditions."""

    def test_string_equality(self) -> None:
        result = where_to_filter({"status": "active"})
        assert result == "status='active'"

    def test_number_equality(self) -> None:
        result = where_to_filter({"score": 90})
        assert result == "score=90"

    def test_boolean_equality(self) -> None:
        result = where_to_filter({"enabled": True})
        assert result == "enabled=true"

    def test_boolean_false(self) -> None:
        result = where_to_filter({"enabled": False})
        assert result == "enabled=false"

    def test_multiple_fields_and(self) -> None:
        result = where_to_filter({"status": "active", "role": "teacher"})
        # Order may vary, but both should be present with AND
        assert "status='active'" in result
        assert "role='teacher'" in result
        assert " AND " in result

    def test_empty_where_returns_none(self) -> None:
        result = where_to_filter({})
        assert result is None


class TestWhereToFilterOperators:
    """Tests for operator conditions."""

    def test_ne_operator(self) -> None:
        result = where_to_filter({"status": {"ne": "deleted"}})
        assert result == "status!='deleted'"

    def test_gt_operator(self) -> None:
        result = where_to_filter({"score": {"gt": 90}})
        assert result == "score>90"

    def test_gte_operator(self) -> None:
        result = where_to_filter({"score": {"gte": 90}})
        assert result == "score>=90"

    def test_lt_operator(self) -> None:
        result = where_to_filter({"score": {"lt": 90}})
        assert result == "score<90"

    def test_lte_operator(self) -> None:
        result = where_to_filter({"score": {"lte": 90}})
        assert result == "score<=90"

    def test_contains_operator(self) -> None:
        result = where_to_filter({"email": {"contains": "@school.edu"}})
        assert result == "email~'@school.edu'"

    def test_multiple_operators_same_field(self) -> None:
        result = where_to_filter({"score": {"gte": 80, "lte": 100}})
        assert "score>=80" in result
        assert "score<=100" in result
        assert " AND " in result


class TestWhereToFilterIn:
    """Tests for in/not_in operators."""

    def test_in_operator_single(self) -> None:
        result = where_to_filter({"role": {"in_": ["teacher"]}})
        assert result == "role='teacher'"

    def test_in_operator_multiple(self) -> None:
        result = where_to_filter({"role": {"in_": ["teacher", "aide"]}})
        assert result == "(role='teacher' OR role='aide')"

    def test_not_in_operator(self) -> None:
        result = where_to_filter({"status": {"not_in": ["deleted", "inactive"]}})
        assert "status!='deleted'" in result
        assert "status!='inactive'" in result
        assert " AND " in result


class TestWhereToFilterOr:
    """Tests for OR conditions."""

    def test_explicit_or(self) -> None:
        result = where_to_filter({"OR": [{"role": "teacher"}, {"status": "active"}]})
        assert result == "role='teacher' OR status='active'"

    def test_nested_or_with_multiple_fields(self) -> None:
        result = where_to_filter(
            {
                "OR": [
                    {"role": "teacher", "status": "active"},
                    {"role": "admin"},
                ]
            }
        )
        # First clause should have AND, joined by OR
        assert "role='teacher'" in result
        assert "status='active'" in result
        assert "role='admin'" in result


class TestWhereToFilterEscaping:
    """Tests for value escaping."""

    def test_single_quote_escaped(self) -> None:
        result = where_to_filter({"name": "O'Brien"})
        assert result == "name='O''Brien'"

    def test_multiple_single_quotes(self) -> None:
        result = where_to_filter({"name": "It's John's"})
        assert result == "name='It''s John''s'"

    def test_consecutive_single_quotes(self) -> None:
        result = where_to_filter({"name": "test''value"})
        assert result == "name='test''''value'"

    def test_quote_at_start(self) -> None:
        result = where_to_filter({"name": "'quoted"})
        assert result == "name='''quoted'"

    def test_quote_at_end(self) -> None:
        result = where_to_filter({"name": "quoted'"})
        assert result == "name='quoted'''"

    def test_datetime_formatted(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = where_to_filter({"created": dt})
        assert "created='2024-01-15T10:30:00'" in result

    def test_date_formatted(self) -> None:
        d = date(2024, 1, 15)
        result = where_to_filter({"birthDate": d})
        assert result == "birthDate='2024-01-15'"

    def test_float_not_quoted(self) -> None:
        result = where_to_filter({"gpa": 3.5})
        assert result == "gpa=3.5"

    def test_unicode_characters(self) -> None:
        result = where_to_filter({"name": "日本語"})
        assert result == "name='日本語'"

    def test_emoji(self) -> None:
        result = where_to_filter({"name": "émoji 🎉"})
        assert result == "name='émoji 🎉'"

    def test_special_characters(self) -> None:
        result = where_to_filter({"email": "user+tag@example.com"})
        assert result == "email='user+tag@example.com'"

    def test_whitespace_preserved(self) -> None:
        result = where_to_filter({"name": "John Doe"})
        assert result == "name='John Doe'"


class TestWhereToFilterNumbers:
    """Tests for number handling."""

    def test_zero(self) -> None:
        result = where_to_filter({"count": 0})
        assert result == "count=0"

    def test_negative_numbers(self) -> None:
        result = where_to_filter({"balance": -100})
        assert result == "balance=-100"

    def test_decimal_numbers(self) -> None:
        import math

        result = where_to_filter({"score": math.pi})
        assert result == f"score={math.pi}"

    def test_empty_string(self) -> None:
        result = where_to_filter({"name": ""})
        assert result == "name=''"


class TestWhereToFilterRealWorld:
    """Tests for real-world use cases."""

    def test_find_active_teachers_at_school(self) -> None:
        result = where_to_filter(
            {"role": "teacher", "status": "active", "orgSourcedIds": "school-123"}
        )
        assert "role='teacher'" in result
        assert "status='active'" in result
        assert "orgSourcedIds='school-123'" in result
        assert result.count(" AND ") == 2

    def test_find_users_modified_after_date(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = where_to_filter({"dateLastModified": {"gt": dt}, "status": "active"})
        assert "dateLastModified>'2024-01-01T00:00:00'" in result
        assert "status='active'" in result

    def test_exclude_deleted_and_archived(self) -> None:
        result = where_to_filter({"status": {"not_in": ["deleted", "archived", "suspended"]}})
        assert "status!='deleted'" in result
        assert "status!='archived'" in result
        assert "status!='suspended'" in result
