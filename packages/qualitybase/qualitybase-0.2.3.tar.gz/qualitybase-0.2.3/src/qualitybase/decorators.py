import importlib


def _import_string(dotted_path, package=None):
    if dotted_path.startswith('.'):
        if not package:
            raise ImportError(f"Cannot import relative path {dotted_path} without package")
        try:
            module = importlib.import_module(dotted_path, package=package)  # nosec B307
            return module
        except (AttributeError, ImportError) as e:
            raise ImportError(f"Cannot import {dotted_path}") from e

    paths_to_try = [dotted_path]
    if package:
        paths_to_try.insert(0, f"{package}.{dotted_path}")

    for path in paths_to_try:
        try:
            module_path, class_name = path.rsplit('.', 1)
            module = importlib.import_module(module_path)  # nosec B307
            return getattr(module, class_name)
        except (AttributeError, ImportError, ValueError):
            continue

    for path in paths_to_try:
        try:
            path_extend = f"{path}.Extend"
            module_path, class_name = path_extend.rsplit('.', 1)
            module = importlib.import_module(module_path)  # nosec B307
            return getattr(module, class_name)
        except (AttributeError, ImportError, ValueError):
            continue

    raise ImportError(f"Cannot import {dotted_path}")


def inherit_class_list(*args):
    def decorator(cls):
        package = cls.__module__ if hasattr(cls, '__module__') else None
        inherit_classes = tuple(_import_string(i, package=package) for i in args)
        bases = (cls,) + inherit_classes
        new_class = type(cls.__name__, bases, {})
        return new_class

    return decorator

__all__ = ["inherit_class_list"]
