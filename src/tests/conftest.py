# conftest.py
import pytest
import os

@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ["save_stats_db"] = "False"
    os.environ["limit_of_dices_per_roll"] =  '100'
    os.environ["limit_of_die_size"] = '100'
