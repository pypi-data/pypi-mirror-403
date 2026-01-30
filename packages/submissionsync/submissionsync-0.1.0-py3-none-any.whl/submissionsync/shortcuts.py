# shortcuts.py
# Provides create_shortcut for Windows .lnk shortcut creation
import win32com.client
from pathlib import Path

def create_shortcut(target: str, shortcut_path: str, working_dir: str = None):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = str(target)
    if working_dir:
        shortcut.WorkingDirectory = str(working_dir)
    shortcut.save()
    if not Path(shortcut_path).exists():
        raise Exception(f"Shortcut creation failed: {shortcut_path}")
