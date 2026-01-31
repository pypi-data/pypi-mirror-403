"""
XApp Protected Module
Auto-detects bytecode location (handles both __pycache__ and direct placement)
Supports Python 3.8 - 3.12
"""

import sys
import importlib.util
from pathlib import Path

def find_bytecode_file():
    """Find the bytecode file in possible locations"""
    module_dir = Path(__file__).parent
    major = sys.version_info.major
    minor = sys.version_info.minor
    
    bytecode_filename = f'xapp_core.cpython-{major}{minor}.pyc'
    
    # Possible locations (in order of preference)
    possible_locations = [
        # Location 1: Standard __pycache__ directory (local development)
        module_dir / '__pycache__' / bytecode_filename,
        
        # Location 2: Direct in module directory (some PyPI packages)
        module_dir / bytecode_filename,
        
        # Location 3: Alternative __pycache__ name
        module_dir / '__pycache__' / f'xapp_core.cpython-{major}{minor}.opt-2.pyc',
    ]
    
    # Find the first location that exists
    for location in possible_locations:
        if location.exists():
            return location, module_dir
    
    return None, module_dir

def list_available_bytecode(module_dir):
    """List all available .pyc files for error messages"""
    available = []
    
    # Check __pycache__ directory
    cache_dir = module_dir / '__pycache__'
    if cache_dir.exists():
        for pyc_file in cache_dir.glob('xapp_core*.pyc'):
            available.append(str(pyc_file.relative_to(module_dir)))
    
    # Check module directory directly
    for pyc_file in module_dir.glob('xapp_core*.pyc'):
        available.append(str(pyc_file.relative_to(module_dir)))
    
    return available

def load_bytecode_module():
    """Load the bytecode module"""
    bytecode_file, module_dir = find_bytecode_file()
    
    if bytecode_file is None:
        # Build helpful error message
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        available = list_available_bytecode(module_dir)
        
        error_msg = f"""
+----------------------------------------------------------------+
�  ? XApp Protected Module - Bytecode Not Found                 �
+----------------------------------------------------------------+

Your Python version: {current_version}
Expected file: xapp_core.cpython-{sys.version_info.major}{sys.version_info.minor}.pyc

"""
        if available:
            error_msg += "?? Available bytecode files:\n"
            for f in available:
                error_msg += f"   � {f}\n"
            error_msg += "\n"
        else:
            error_msg += """
?? No bytecode files found in package!

Checked locations:
   � {module_dir}/__pycache__/
   � {module_dir}/

This is likely a packaging error.

"""
        
        error_msg += f"""
?? Solutions:
   1. Install a compatible Python version, OR
   2. Contact the package maintainer

?? Module directory: {module_dir}
???????????????????????????????????????????????????????????????
"""
        raise ImportError(error_msg)
    
    # Load the bytecode module
    try:
        spec = importlib.util.spec_from_file_location("xapp_core", bytecode_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load module spec from {bytecode_file}")
        
        core_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core_module)
        
        return core_module
    
    except Exception as e:
        error_msg = f"""
+----------------------------------------------------------------+
�  ? XApp Protected Module - Load Error                         �
+----------------------------------------------------------------+

Failed to load: {bytecode_file.name}
Location: {bytecode_file}

Error: {str(e)}

?? Try reinstalling:
   pip uninstall xapp-protected
   pip install xapp-protected

???????????????????????????????????????????????????????????????
"""
        raise ImportError(error_msg) from e

# Load the core module
_core_module = load_bytecode_module()

# Export the create_app function
create_app = _core_module.create_app

# Module metadata
__version__ = "0.1.4"
__author__ = "Mr Void"

__all__ = ['create_app']