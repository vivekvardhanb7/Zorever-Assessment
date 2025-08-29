import os
from src.helpers import load_properties, find_property

def test_load_and_lookup():
    root = os.path.dirname(__file__)
    data_dir = os.path.join(os.path.dirname(root), "data")
    df = load_properties(os.path.join(data_dir, "properties.csv"))
    # Property by ID
    prop = find_property(df, "P003")
    assert prop is not None
    assert prop.get("property_name") == "Marina Studio"
