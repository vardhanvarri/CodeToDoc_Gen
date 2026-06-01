"""
PythonAnywhere WSGI entry point.

In the PythonAnywhere Web tab, point your WSGI file at this module
or copy its contents into your site WSGI configuration file.
"""

import sys
from pathlib import Path

# Update YOUR_USERNAME to your PythonAnywhere username.
PROJECT_DIR = Path("/home/vardhanvarri/doc_gen")

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app import application  # noqa: E402
