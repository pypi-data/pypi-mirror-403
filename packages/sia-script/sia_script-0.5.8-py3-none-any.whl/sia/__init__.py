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

# Import core modules if available
try:
    from . import qbt
    from . import vqram
    from . import ntt
    # Import the new ELS modules
    from . import els_core
    from . import els_parser
    # Re-export the main ELS functions for backward compatibility
    from .els_core import (
        run,
        run_file,
        safe_run,
        repl,
        extract_sia_block,
        ABAPType,
        TypedVariable,
        RuntimeEnv,
        RuntimeError,
        SystemVariables,
        SelectionOption
    )
except ImportError:
    pass

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
    # ELS exports
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
    "SelectionOption",
    # Parser exports (optional)
    "els_core",
    "els_parser"
]

# For backward compatibility, also export 'els' as an alias pointing to els_core
try:
    import sys
    sys.modules[__name__ + '.els'] = sys.modules[__name__ + '.els_core']
except:
    pass