"""Example WSGI entry point for PythonAnywhere.

Update the path below to match your PythonAnywhere username and project path,
then copy the relevant lines into your PythonAnywhere WSGI configuration file.
"""

import sys

PROJECT_HOME = "/home/yourusername/Personal-Finance-Manager-V.1"

if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

from app import app as application
