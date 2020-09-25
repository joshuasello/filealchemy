import os, platform

# os.getenv() Availability: most flavors of Unix, Windows.
SYS_PLATFORM = platform.system()
SYS_USER = os.getenv("username")
SYS_MACHINE = platform.machine()
SYS_PROCESSOR = platform.processor()
SYS_NODE = platform.node()  # network name (may not be fully qualified!). Empty if the value can't be determined.

PY_PATH = os.getenv("PYTHONPATH")
PY_VERSION = platform.python_version()
PY_COMPILER = platform.python_compiler()

print(PY_VERSION)
