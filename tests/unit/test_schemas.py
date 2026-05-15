"""Unit tests for Pydantic schema validators."""
import pytest
from pydantic import ValidationError
from app.schemas.order import OrderCreate, OrderUpdate


class TestOrderCreateValidation:
    def test_valid_order(self):
        o = OrderCreate(
            patient_first_name="Marie",
            patient_last_name="Curie",
            patient_dob="12/05/1900",
        )
        assert o.patient_first_name == "Marie"

    def test_strips_whitespace_from_name(self):
        o = OrderCreate(
            patient_first_name="  Marie  ",
            patient_last_name="  Curie  ",
            patient_dob="12/05/1900",
        )
        assert o.patient_first_name == "Marie"
        assert o.patient_last_name == "Curie"

    def test_rejects_empty_first_name(self):
        with pytest.raises(ValidationError, match="empty"):
            OrderCreate(
                patient_first_name="   ",
                patient_last_name="Curie",
                patient_dob="12/05/1900",
            )

    def test_rejects_empty_last_name(self):
        with pytest.raises(ValidationError, match="empty"):
            OrderCreate(
                patient_first_name="Marie",
                patient_last_name="",
                patient_dob="12/05/1900",
            )

    def test_rejects_name_with_digits(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            OrderCreate(
                patient_first_name="Marie123",
                patient_last_name="Curie",
                patient_dob="12/05/1900",
            )

    def test_rejects_name_too_long(self):
        with pytest.raises(ValidationError, match="100 characters"):
            OrderCreate(
                patient_first_name="A" * 101,
                patient_last_name="Curie",
                patient_dob="12/05/1900",
            )

    def test_allows_hyphenated_name(self):
        o = OrderCreate(
            patient_first_name="Mary-Jane",
            patient_last_name="O'Brien",
            patient_dob="01/01/1990",
        )
        assert o.patient_first_name == "Mary-Jane"
        assert o.patient_last_name == "O'Brien"

    def test_rejects_empty_dob(self):
        with pytest.raises(ValidationError, match="empty"):
            OrderCreate(
                patient_first_name="Marie",
                patient_last_name="Curie",
                patient_dob="  ",
            )

    def test_rejects_dob_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            OrderCreate(
                patient_first_name="Marie",
                patient_last_name="Curie",
                patient_dob="A" * 51,
            )


class TestOrderUpdateValidation:
    def test_partial_update_first_name_only(self):
        u = OrderUpdate(patient_first_name="Jane")
        assert u.patient_first_name == "Jane"
        assert u.patient_last_name is None
        assert u.patient_dob is None

    def test_partial_update_all_none(self):
        u = OrderUpdate()
        assert u.patient_first_name is None
        assert u.patient_last_name is None

    def test_rejects_invalid_name_in_update(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            OrderUpdate(patient_first_name="John$$")

    def test_allows_none_values(self):
        u = OrderUpdate(patient_first_name=None, patient_last_name=None)
        assert u.patient_first_name is None
