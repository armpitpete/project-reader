import pytest

from project_reader.models import WorkItem, WorkState


def test_work_item_requires_positive_weight() -> None:
    with pytest.raises(ValueError):
        WorkItem("Invalid", WorkState.TODO, 0)
