from typing import Dict, Type, Any, List, Tuple
from termcolor import cprint
import inspect

_PLUGIN_REGISTRY: Dict[str, Type] = {}


def register_plugin(cls: Type) -> Type:
    """
    Usage:
        @register_plugin
        class MyPlugin(VisualizerModule):
            # Dependency declaration
            requires_robot_vis = True
            
            # plugin configuration
            TOPIC_NAME = "/my/topic"
            UPDATE_RATE = 30
            
            def __init__(self, server, robot_vis=None):
                super().__init__("My Plugin", server)
                self.robot_vis = robot_vis
                self.topic_name = self.TOPIC_NAME
                ...
    
    args:
        cls: the plugin class to register
        
    returns:
        the same class (decorator doesn't modify it)
    """
    if not hasattr(cls, '__name__'):
        raise ValueError("Plugin class must have a __name__ attribute")
    
    plugin_name = cls.__name__
    if plugin_name in _PLUGIN_REGISTRY:
        cprint(f"Warning: Plugin '{plugin_name}' is already registered. Overwriting.", 'yellow')
    
    _PLUGIN_REGISTRY[plugin_name] = cls
    return cls


def get_registered_plugins() -> Dict[str, Type]:
    return _PLUGIN_REGISTRY.copy()


def clear_registry() -> None:
    _PLUGIN_REGISTRY.clear()


class PluginInstantiator:
    @staticmethod
    def instantiate_plugin(plugin_cls: Type, server: Any) -> Any:
        try:
            return plugin_cls(server)
        except TypeError as e:
            cprint(f"Error instantiating plugin {plugin_cls.__name__}: {e}", 'red')
            cprint(f"Plugin __init__ signature: {inspect.signature(plugin_cls.__init__)}", 'yellow')
            raise


def discover_and_instantiate_plugins(server: Any) -> Tuple[List[Any], List[Dict[str, str]]]:
    """
    Discover and instantiate all registered plugins.
    
    Returns:
        Tuple of (plugin_instances, plugin_status_info)
    """
    plugins = []
    instantiator = PluginInstantiator()
    plugin_status = []
    
    for plugin_name, plugin_cls in _PLUGIN_REGISTRY.items():
        try:
            plugin_instance = instantiator.instantiate_plugin(plugin_cls, server)
            plugins.append(plugin_instance)
            plugin_status.append({'name': plugin_name, 'status': 'registered'})
        except Exception as e:
            plugin_status.append({'name': plugin_name, 'status': f'failed: {e}'})
    
    # Return plugin instances and status info instead of printing
    return plugins, plugin_status

