import importlib
from django.urls import resolve


class ComponentManager:
    def __init__(self, request, app_name=None, key=None):
        self.request = request
        self.app_name = app_name
        self.key = key

    def _session_key(self, name):
        return f"component_state__{name}"

    def load_component(self, name):
        try:
            if self.app_name:
                app_name = self.app_name
            else:
                app_name = str(self.request.resolver_match._func_path).split(".")[0]
            module = importlib.import_module(f"{app_name}.components.{name}")

            component_class = getattr(module, self._class_name(name))

            state = self.request.session.get(self._session_key(name), {})
            component = component_class()

            for key, value in state.items():
                setattr(component, key, value)

            return component
        except (ModuleNotFoundError, AttributeError) as e:
            raise Exception(f"Component '{name}' not found: {e}")

    def save_component(self, name, component):
        state = {
            key: getattr(component, key)
            for key in dir(component)
            if not key.startswith("__") and not callable(getattr(component, key))
        }
        if "form" in state:
            del state["form"]
        if "request" in state:
            del state["request"]
        self.request.session[self._session_key(name)] = state

    def _class_name(self, name):
        name = name.split("_")
        name = [n.capitalize() for n in name]
        name = "".join(name)
        return f"{name}Component"
