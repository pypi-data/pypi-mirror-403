"""Tests for InMemoryQuerySet."""

import pytest
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from virtualqueryset import VirtualQuerySet as InMemoryQuerySet  # type: ignore[assignment]


class MockModel:
    """Mock model for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.django_db
class TestInMemoryQuerySet:
    """Tests for InMemoryQuerySet."""

    def test_init_with_data(self):
        """Test initialization with data."""
        data = [MockModel(name="Alice"), MockModel(name="Bob")]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        assert len(qs) == 2
        assert qs.count() == 2

    def test_filter_exact(self):
        """Test filter with exact lookup."""
        data = [
            MockModel(name="Alice", age=30),
            MockModel(name="Bob", age=25),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.filter(name="Alice")
        assert result.count() == 1
        assert result.first().name == "Alice"

    def test_filter_icontains(self):
        """Test filter with icontains lookup."""
        data = [
            MockModel(name="Alice Smith"),
            MockModel(name="Bob Jones"),
            MockModel(name="alice brown"),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.filter(name__icontains="alice")
        assert result.count() == 2

    def test_filter_in(self):
        """Test filter with in lookup."""
        data = [
            MockModel(id=1, name="Alice"),
            MockModel(id=2, name="Bob"),
            MockModel(id=3, name="Charlie"),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.filter(id__in=[1, 3])
        assert result.count() == 2

    def test_filter_gt(self):
        """Test filter with gt lookup."""
        data = [
            MockModel(age=20),
            MockModel(age=30),
            MockModel(age=40),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.filter(age__gt=25)
        assert result.count() == 2

    def test_order_by(self):
        """Test ordering."""
        data = [
            MockModel(name="Charlie", age=30),
            MockModel(name="Alice", age=25),
            MockModel(name="Bob", age=35),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.order_by("name")
        assert result.first().name == "Alice"
        assert result.last().name == "Charlie"

    def test_order_by_descending(self):
        """Test descending order."""
        data = [
            MockModel(age=20),
            MockModel(age=30),
            MockModel(age=40),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.order_by("-age")
        assert result.first().age == 40
        assert result.last().age == 20

    def test_get_single(self):
        """Test get with single result."""
        data = [
            MockModel(id=1, name="Alice"),
            MockModel(id=2, name="Bob"),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.get(id=1)
        assert result.name == "Alice"

    def test_get_not_found(self):
        """Test get raises ObjectDoesNotExist."""
        data = [MockModel(id=1, name="Alice")]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        with pytest.raises(ObjectDoesNotExist):
            qs.get(id=999)

    def test_get_multiple(self):
        """Test get raises MultipleObjectsReturned."""
        data = [
            MockModel(status="active"),
            MockModel(status="active"),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        with pytest.raises(MultipleObjectsReturned):
            qs.get(status="active")

    def test_slicing(self):
        """Test queryset slicing."""
        data = [MockModel(id=i) for i in range(10)]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs[2:5]
        assert result.count() == 3
        assert result.first().id == 2

    def test_first_last(self):
        """Test first() and last()."""
        data = [MockModel(id=1), MockModel(id=2), MockModel(id=3)]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        assert qs.first().id == 1
        assert qs.last().id == 3

    def test_exists(self):
        """Test exists()."""
        qs_empty = InMemoryQuerySet(model=MockModel, data=[])
        qs_full = InMemoryQuerySet(model=MockModel, data=[MockModel(id=1)])

        assert not qs_empty.exists()
        assert qs_full.exists()

    def test_values(self):
        """Test values()."""
        data = [MockModel(name="Alice", age=30)]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.values("name", "age")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_values_list(self):
        """Test values_list()."""
        data = [MockModel(name="Alice", age=30)]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.values_list("name", "age")
        assert result[0] == ("Alice", 30)

    def test_values_list_flat(self):
        """Test values_list with flat=True."""
        data = [MockModel(name="Alice"), MockModel(name="Bob")]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.values_list("name", flat=True)
        assert result == ["Alice", "Bob"]

    def test_exclude(self):
        """Test exclude()."""
        data = [
            MockModel(name="Alice", active=True),
            MockModel(name="Bob", active=False),
        ]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.exclude(active=False)
        assert result.count() == 1
        assert result.first().name == "Alice"

    def test_none(self):
        """Test none()."""
        data = [MockModel(name="Alice")]
        qs = InMemoryQuerySet(model=MockModel, data=data)

        result = qs.none()
        assert result.count() == 0
