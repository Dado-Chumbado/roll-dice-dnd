import os
import importlib
import logging

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        #TODO: Check this
        return self.__class__.__name__

    def commands_plugin(self, bot):
        @bot.event
        async def on_ready():
            logging.debug(
                f"{self.__class__.__name__} loaded!")


# Load Plugins Dynamically
def load_plugins(plugin_folder="src/plugins"):
    """
    Dynamically loads plugin modules from a specified folder.

    This function walks through the given `plugin_folder` and identifies all `plugin_main.py`
    files. For each such file, it loads the module and attempts to find a class inside it that
    follows the `Plugin{ModuleName}` naming pattern (e.g., `PluginMain` for a file named
    `plugin_main.py`). If found, the class is appended to a list of plugins, which is returned.

    Args:
        plugin_folder (str): The directory path where plugins are stored.

    Returns:
        List: A list of plugin classes ready for instantiation.
    """
    plugins = []
    for root, dirs, files in os.walk(plugin_folder):
        for file in files:
            if file.startswith("plugin_") and file.endswith(".py"):
                plugin_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                spec = importlib.util.spec_from_file_location(module_name,
                                                              plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Automatically instantiate the plugin class (e.g., PluginHelloWorld)
                # Assuming the plugin class follows a naming convention like Plugin{ModuleName}
                plugin_class_name = module_name.title().replace("_", "")
                if hasattr(module, plugin_class_name):
                    plugin_class = getattr(module, plugin_class_name)  # Get the plugin class
                    plugins.append(plugin_class)  # Append the class, not the module
    return plugins

