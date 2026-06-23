"""Tests for src.services.candidate_mapper – Phase 3 coverage."""

from src.models.restaurant import Restaurant
from src.services.candidate_mapper import restaurant_to_dto, restaurants_to_dtos


def _sample_restaurant() -> Restaurant:
    return Restaurant(
        id="42",
        name="Jalsa",
        location="Banashankari",
        cuisines=["North Indian", "Chinese"],
        cost_for_two=600,
        rating=4.2,
        votes=800,
        rest_type="Casual Dining",
        dish_liked="Paneer Butter Masala, Biryani",
        online_order=True,
        book_table=False,
    )


class TestRestaurantToDto:
    def test_maps_all_fields(self):
        dto = restaurant_to_dto(_sample_restaurant())
        assert dto["id"] == "42"
        assert dto["name"] == "Jalsa"
        assert dto["location"] == "Banashankari"
        assert dto["cuisines"] == "North Indian, Chinese"
        assert dto["rate"] == 4.2
        assert dto["votes"] == 800
        assert dto["approx_cost_for_two"] == 600
        assert dto["rest_type"] == "Casual Dining"
        assert dto["dish_liked"] == "Paneer Butter Masala, Biryani"
        assert dto["online_order"] is True
        assert dto["book_table"] is False

    def test_cuisines_joined_as_string(self):
        dto = restaurant_to_dto(_sample_restaurant())
        assert isinstance(dto["cuisines"], str)

    def test_empty_cuisines(self):
        r = Restaurant(id="1", name="X", cuisines=[])
        dto = restaurant_to_dto(r)
        assert dto["cuisines"] == ""

    def test_none_optional_fields_become_empty(self):
        r = Restaurant(id="1", name="X", rest_type=None, dish_liked=None)
        dto = restaurant_to_dto(r)
        assert dto["rest_type"] == ""
        assert dto["dish_liked"] == ""


class TestRestaurantsToDtos:
    def test_batch_conversion(self):
        restaurants = [_sample_restaurant(), _sample_restaurant()]
        dtos = restaurants_to_dtos(restaurants)
        assert len(dtos) == 2
        assert all(isinstance(d, dict) for d in dtos)

    def test_empty_list(self):
        assert restaurants_to_dtos([]) == []
