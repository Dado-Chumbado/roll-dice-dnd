## Plugin Creation Guide

### 1) Folder Structure
Each plugin should reside in a unique folder inside the `plugins` directory. The main file in the folder must be named `plugin_main.py`.

### 2) Plugin Class Requirements
- The main class in `plugin_main.py` should follow the pattern:
  - **Class Name:** `PluginMain` (Combine `Plugin` + CustomName).
  - **Inherits:** `Plugin` class (from `plugin_manager.py`).
  
### 3) Required Method
Override the method:
```python
def commands_plugin(self, bot):
    # Define bot commands here
```

### 4) Tests
Include a `tests/` folder for unit tests. Test files should follow `test_*.py` naming for `pytest` discovery.

---

### Example Structure:
```
plugins/
  my_plugin/
    plugin_main.py
    tests/
      test_my_plugin.py
```

