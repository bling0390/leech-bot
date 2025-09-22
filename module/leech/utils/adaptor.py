from pathlib import Path
from importlib import import_module


def setup_services(relative_path: str, filter_key: str, func_key: str):
    services = {}

    for path in sorted(Path(relative_path).rglob("*.py")):
        exports = vars(import_module('.'.join(path.parent.parts + (path.stem,))))

        if exports.get(filter_key) and exports.get(func_key):
            services[exports[filter_key]] = exports[func_key]

    return services
