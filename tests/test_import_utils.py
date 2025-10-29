"""
Unit-tests helper functions in your import route: _str_to_bool, _parse_csv, _parse_json.
No DB or tenant checks here (that’s for integration)
"""

# mini_ddq_app/tests/test_import_utils.py
from mini_ddq_app.routes.imports import _str_to_bool, _parse_csv, _parse_json

def test_str_to_bool_variants():
    true_vals = ["1","true","True","YES","y"]
    false_vals = ["0","false","False","no","N"]
    for v in true_vals:
        assert _str_to_bool(v) is True
    for v in false_vals:
        assert _str_to_bool(v) is False
    assert _str_to_bool(None) is None
    assert _str_to_bool("maybe") is None

def test_parse_csv_basic():
    csv_bytes = b"questionnaire_id,text,category,is_required,display_order\n" \
                b"q1,Hello,cat,true,3\n" \
                b"q1,World,,false,\n"
    rows = _parse_csv(csv_bytes)
    assert len(rows) == 2
    assert rows[0]["questionnaire_id"] == "q1"
    assert rows[0]["text"] == "Hello"
    assert rows[0]["is_required"] is True
    assert rows[0]["display_order"] == 3
    assert rows[1]["display_order"] is None

def test_parse_json_basic():
    data = [
        {"questionnaire_id": "q1", "text": "Hi", "category": "c", "is_required": "true", "display_order": 1},
        {"questionnaire_id": "q1", "text": "There", "is_required": "false"}
    ]
    import json
    rows = _parse_json(json.dumps(data).encode("utf-8"))
    assert len(rows) == 2
    assert rows[0]["is_required"] is True
    assert rows[1]["display_order"] is None