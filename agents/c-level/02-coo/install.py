"""Compatibility command for the canonical COO profile."""
from pathlib import Path
import subprocess
import sys
if __name__=='__main__':
    root=Path(__file__).resolve().parents[3]
    raise SystemExit(subprocess.call([sys.executable,str(root/'agents/install.py'),'mars-coo',*sys.argv[1:]]))
