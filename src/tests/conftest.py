# conftest.py
import os
import sys

# Set env vars at module level BEFORE any other imports to prevent DB connection
os.environ["save_stats_db"] = ""
os.environ["limit_of_dice_per_roll"] = '100'
os.environ["limit_of_die_size"] = '100'

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ["save_stats_db"] = ""
    os.environ["limit_of_dice_per_roll"] =  '100'
    os.environ["limit_of_die_size"] = '100'


