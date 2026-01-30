import os
import argparse
import importlib.util
from processor_tools.config_io import build_configdir


def main():
    parser = argparse.ArgumentParser(description="Initialise a config directory for a package.")
    parser.add_argument("package_name", help="Name of the package (used for config dir name)")
    parser.add_argument("configs_module", help="Python module path containing CONFIGS dict")
    parser.add_argument("--config_dir", help="Config directory path (default: ~/.<package_name>)", default=None)
    args = parser.parse_args()

    # Dynamically import the configs dict from the given module
    spec = importlib.util.spec_from_file_location("configs_module", args.configs_module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    CONFIGS = getattr(module, "CONFIGS")

    config_dir = args.config_dir or os.path.join(os.path.expanduser("~"), f".{args.package_name}")
    print(f"Initializing config directory at {config_dir}")
    build_configdir(config_dir, configs=CONFIGS, exists_skip=True)
    print("Config files initialized.")

if __name__ == "__main__":
    main()
