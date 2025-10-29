# mini_ddq_app/tests/test_db_dep.py
import pytest
from sqlalchemy import text
from mini_ddq_app.db import get_db

def test_get_db_yield_and_close():
    gen = get_db()
    session = next(gen)
    # basic sanity query
    assert session.execute(text("SELECT 1")).scalar() == 1
    # exhaust the generator to hit the finally/close path
    with pytest.raises(StopIteration):
        next(gen)