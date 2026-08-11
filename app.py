"""Streamlit entrypoint: runs the dashboard living in src/app.py.

Keeps the app source under src/ while exposing a root app.py so the
project can be deployed on Streamlit Cloud (which runs ./app.py by default).
"""

import os
import runpy
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
runpy.run_path(
    os.path.join(os.path.dirname(__file__), "src", "app.py"), run_name="__main__"
)
