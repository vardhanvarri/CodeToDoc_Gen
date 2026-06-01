# ============================================================
# COPY THIS ENTIRE FILE into PythonAnywhere WSGI config:
#   Web tab → WSGI configuration file
# Replace the line:  from test import app as application
# ============================================================

import sys

sys.path.insert(0, "/home/vardhanvarri/doc_gen")

from app import application
