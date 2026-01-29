# src/devopsmind/programs/core/rule_loader.py

import importlib
from types import ModuleType


def load_program_module(program: str, module_name: str) -> ModuleType:
    """
    Load a program-specific module, e.g.:

    programs.buildtrack.coverage_rules
    programs.infrahack.validation_rules
    """
    module_path = f"devopsmind.programs.{program}.{module_name}"

    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise RuntimeError(
            f"Program '{program}' does not define '{module_name}.py'"
        ) from e
