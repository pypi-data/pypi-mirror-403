
### `tests/test_datasets.py`

from centraltechpack import list_datasets, load_dataset

def test_list():
    items = list_datasets()
    assert any(x["name"] == "medicine" for x in items)

def test_load():
    data = load_dataset("medicine")
    assert len(data) >= 1
    assert "id" in data[0]
