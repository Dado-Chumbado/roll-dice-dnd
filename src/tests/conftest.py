# conftest.py
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ["save_stats_db"] = "False"
    os.environ["limit_of_dice_per_roll"] =  '100'
    os.environ["limit_of_die_size"] = '100'


