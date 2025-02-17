import importlib
import pkgutil
import modules

def load_modules():
    """
    Dynamically loads all security modules from the 'modules' package.

    :return: Dictionary {module_name: module_class}
    """
    loaded_modules = {}

    package_path = modules.__path__
    package_name = modules.__name__

    for _, module_name, _ in pkgutil.iter_modules(package_path):
        full_module_name = f"{package_name}.{module_name}"
        module = importlib.import_module(full_module_name)
        
        # Assumes each module defines a class with the same name as the file
        class_name = "".join(word.capitalize() for word in module_name.split("_"))  # Convert snake_case to CamelCase
        module_class = getattr(module, class_name, None)

        if module_class:
            loaded_modules[module_name] = module_class
        else:
            print(f"Warning: Could not find class '{class_name}' in module '{full_module_name}'")

    return loaded_modules