import importlib
import inspect
import os
from typing import List, Optional, Type

from .base import BaseConverter


def get_all_converters() -> List[Type[BaseConverter]]:
    """
    Dynamically discovers all BaseConverter subclasses in the current package.
    """
    converters = []
    package_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(package_dir):
        if filename.endswith('.py') and filename not in ('__init__.py', 'base.py'):
            module_name = f".{filename[:-3]}"
            try:
                module = importlib.import_module(module_name, package=__package__)
                for _name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseConverter) and 
                        obj is not BaseConverter):
                        converters.append(obj)
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
                
    return converters

def get_converter_for_file(file_path: str) -> Optional[BaseConverter]:
    """
    Identifies the provider for a given file and returns an instance of its converter.
    Returns None if no provider is identified.
    """
    for converter_cls in get_all_converters():
        converter = converter_cls()
        if converter.detect(file_path):
            return converter
    return None
