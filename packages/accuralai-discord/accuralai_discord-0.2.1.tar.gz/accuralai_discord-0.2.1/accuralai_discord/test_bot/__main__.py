"""Entry point for running test_bot as a module.

This allows `python -m accuralai_discord.test_bot` to work even though
test_bot is both a package (directory) and a module (test_bot.py).
"""

import importlib.util
import sys
from pathlib import Path

# Get the path to the sibling test_bot.py file
_package_dir = Path(__file__).parent.parent
_test_bot_module_path = _package_dir / "test_bot.py"

# Load the module from the file
_spec = importlib.util.spec_from_file_location("accuralai_discord._test_bot_module", _test_bot_module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load test_bot module from {_test_bot_module_path}")

_test_bot_module = importlib.util.module_from_spec(_spec)
sys.modules["accuralai_discord._test_bot_module"] = _test_bot_module
_spec.loader.exec_module(_test_bot_module)

# Run the main function
if __name__ == "__main__":
    _test_bot_module.main()

