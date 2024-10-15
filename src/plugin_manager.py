import os
import importlib


class Plugin:
    def __init__(self, bot):
        self.bot = bot


# Load Plugins Dynamically
def load_plugins(plugin_folder="src/plugins"):
    plugins = []
    for root, dirs, files in os.walk(plugin_folder):
        for file in files:
            if file == "plugin_main.py":
                plugin_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                spec = importlib.util.spec_from_file_location(module_name,
                                                              plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Automatically instantiate the plugin class (e.g., PluginHelloWorld)
                # Assuming the plugin class follows a naming convention like Plugin{ModuleName}
                plugin_class_name = module_name.title().replace("_", "")
                print("module:", module, "plugin_class_name:", plugin_class_name)
                if hasattr(module, plugin_class_name):
                    plugin_class = getattr(module, plugin_class_name)  # Get the plugin class
                    plugins.append(plugin_class)  # Append the class, not the module
    return plugins

