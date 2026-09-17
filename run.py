"""Wrapper for Render deployment - runs dashboard/app.py"""
import os, sys, subprocess
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, os.path.join(ROOT, "dashboard", "app.py")]))
