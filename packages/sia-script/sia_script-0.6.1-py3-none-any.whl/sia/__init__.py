"""
HDQS Quantum Computing Library
Hyper-Dimensional Quantum System Client

Default Server: 31.97.239.213:8000
"""

__version__ = "1.0.0"
__author__ = "Sia Software Innovations Private Limited"
__server_ip__ = "31.97.239.213"
__server_port__ = 8000
__default_url__ = f"http://{__server_ip__}:{__server_port__}"

# First import hdqs components that should always exist
from .hdqs import (
    HDQSClient,
    LocalHDQSClient,
    HDQSError,
    connect,
    hdqs,
    call,
    create_circuit,
    run_circuit,
    measure,
    analyze,
    run_demo,
    create_hyper_system,
    DEFAULT_SERVER_IP,
    DEFAULT_SERVER_PORT,
    DEFAULT_BASE_URL
)

# Initialize ELS exports as None first
run = None
run_file = None
safe_run = None
repl = None
extract_sia_block = None
ABAPType = None
TypedVariable = None
RuntimeEnv = None
RuntimeError = None
SystemVariables = None
SelectionOption = None

# Try to import ELS modules separately
try:
    from . import els_core
    
    # Import main functions from els_core
    from .els_core import (
        run as run_func,
        run_file as run_file_func,
        safe_run as safe_run_func,
        repl as repl_func,
        extract_sia_block as extract_sia_block_func,
        ABAPType as ABAPType_class,
        TypedVariable as TypedVariable_class,
        RuntimeEnv as RuntimeEnv_class,
        RuntimeError as RuntimeError_class,
        SystemVariables as SystemVariables_class,
        SelectionOption as SelectionOption_class
    )
    
    # Assign to module-level variables
    run = run_func
    run_file = run_file_func
    safe_run = safe_run_func
    repl = repl_func
    extract_sia_block = extract_sia_block_func
    ABAPType = ABAPType_class
    TypedVariable = TypedVariable_class
    RuntimeEnv = RuntimeEnv_class
    RuntimeError = RuntimeError_class
    SystemVariables = SystemVariables_class
    SelectionOption = SelectionOption_class
    
except ImportError as e:
    # Silently ignore ELS import errors - they're optional
    pass

# Try to import other optional modules
try:
    from . import qbt
except ImportError:
    qbt = None

try:
    from . import vqram
except ImportError:
    vqram = None

try:
    from . import ntt
except ImportError:
    ntt = None

__all__ = [
    "HDQSClient",
    "LocalHDQSClient",
    "HDQSError",
    "connect",
    "hdqs",
    "call",
    "create_circuit",
    "run_circuit",
    "measure",
    "analyze",
    "run_demo",
    "create_hyper_system",
    "DEFAULT_SERVER_IP",
    "DEFAULT_SERVER_PORT",
    "DEFAULT_BASE_URL",
    "qbt",
    "vqram",
    "ntt",
    # ELS exports (will be None if not imported)
    "run",
    "run_file",
    "safe_run",
    "repl",
    "extract_sia_block",
    "ABAPType",
    "TypedVariable",
    "RuntimeEnv",
    "RuntimeError",
    "SystemVariables",
    "SelectionOption"
]

# For backward compatibility, create els module alias if els_core exists
if els_core is not None:
    import sys
    sys.modules[__name__ + '.els'] = sys.modules[__name__ + '.els_core']