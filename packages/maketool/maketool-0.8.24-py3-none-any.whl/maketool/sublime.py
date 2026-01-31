import os
import argparse
import json
# import shutil
import psutil
import subprocess
from typing import Any, Optional

def _standard_user_packages_dir() -> Optional[str]:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return os.path.join(appdata, "Sublime Text", "Packages", "User")


def _find_sublime_exe_from_path() -> Optional[str]:
    # Try PATH: "sublime_text.exe" or "subl" shim
    for cmd in (["where", "sublime_text.exe"], ["where", "subl"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                exe = r.stdout.splitlines()[0].strip()
                if os.path.exists(exe):
                    return exe
        except Exception:
            pass
    return None


def _find_sublime_exe_from_registry() -> Optional[str]:
    # Best-effort uninstall registry search (Windows)
    try:
        import winreg  # type: ignore
    except Exception:
        return None

    roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    def scan(root, subkey) -> Optional[str]:
        try:
            with winreg.OpenKey(root, subkey) as k:
                n = winreg.QueryInfoKey(k)[0]
                for i in range(n):
                    try:
                        sk = winreg.EnumKey(k, i)
                        with winreg.OpenKey(k, sk) as kk:
                            try:
                                name = winreg.QueryValueEx(kk, "DisplayName")[0]
                            except Exception:
                                continue
                            if "sublime text" not in str(name).lower():
                                continue

                            # Prefer InstallLocation if present
                            try:
                                il = winreg.QueryValueEx(kk, "InstallLocation")[0]
                                if il:
                                    exe = os.path.join(str(il), "sublime_text.exe")
                                    if os.path.exists(exe):
                                        return exe
                            except Exception:
                                pass

                            # Fallback: DisplayIcon often points to exe
                            try:
                                di = winreg.QueryValueEx(kk, "DisplayIcon")[0]
                                if di:
                                    di = str(di).strip().strip('"').split(",")[0]
                                    if os.path.exists(di):
                                        return di
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    for root, sub in roots:
        exe = scan(root, sub)
        if exe:
            return exe
    return None


def _find_running_sublime_exe():
    for p in psutil.process_iter(["name", "exe"]):
        if p.info["name"] and p.info["name"].lower() == "sublime_text.exe":
            return p.info["exe"]
    return None

def _detect_user_packages_dir() -> str:
    # Prefer an exe-based decision (portable vs normal) when possible.
    exe = (
        _find_running_sublime_exe()  # best if available
        or _find_sublime_exe_from_registry()
        or _find_sublime_exe_from_path()
    )

    if exe:
        exe_dir = os.path.dirname(exe)
        portable_root = os.path.join(exe_dir, "Data")
        if os.path.isdir(portable_root):
            return os.path.join(portable_root, "Packages", "User")
        # Not portable -> standard location
        standard = _standard_user_packages_dir()
        if standard:
            return standard

    # If we couldn't locate the exe, fall back to standard if it exists.
    standard = _standard_user_packages_dir()
    if standard:
        return standard

    raise RuntimeError(
        "Could not auto-detect Sublime Text Packages\\User directory.\n"
        "Open Sublime -> Preferences -> Browse Packages to locate it."
    )


def _load_json_or_empty(path: str) -> Any:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If the file exists but isn't valid JSON, do not destroy it here.
        # Caller will still back up before writing.
        return []


# def _backup(path: str) -> None:
#     if os.path.exists(path):
#         backup_path = path + ".bak"
#         shutil.copy2(path, backup_path)
#         print(f"Backed up: {backup_path}")


def _upsert_keybindings(existing: list[dict], updates: list[dict]) -> list[dict]:
    """
    Update/insert keybindings by matching on ("keys","command").
    Leaves unrelated user bindings untouched.
    """
    out = list(existing) if isinstance(existing, list) else []

    def key_id(item: dict) -> tuple:
        return (tuple(item.get("keys", [])), item.get("command"))

    index = {key_id(k): i for i, k in enumerate(out) if isinstance(k, dict)}

    for upd in updates:
        kid = key_id(upd)
        if kid in index:
            out[index[kid]] = upd
        else:
            out.append(upd)
    return out

def _prune_maketool_bindings(existing: list[dict], maketool: list[dict]) -> list[dict]:
    """
    Remove existing bindings that represent the same maketool intent
    (command + args.variant), regardless of key.
    """
    def intent(item: dict) -> tuple:
        return (
            item.get("command"),
            (item.get("args") or {}).get("variant")
        )

    maketool_intents = {intent(m) for m in maketool}

    out = []
    for item in existing:
        if not isinstance(item, dict):
            out.append(item)
            continue
        if intent(item) in maketool_intents:
            continue
        out.append(item)

    return out


def process(user_packages_dir: str) -> None:
    os.makedirs(user_packages_dir, exist_ok=True)

    keymap_file_path = os.path.join(user_packages_dir, "Default (Windows).sublime-keymap")

    # Maketool-owned bindings (preserve these keys exactly as requested)
    maketool_bindings = [
        {
            "keys": ["f1"],
            "command": "run_macro_file",
            "args": {"file": "Packages/User/print-python.sublime-macro"},
            "context": [{"key": "selector", "operator": "equal", "operand": "source.python"}]
        },
        {
            "keys": ["ctrl+backspace"],
            "command": "run_macro_file",
            "args": {"file": "res://Packages/Default/Delete Line.sublime-macro"}
        },
        {
            "keys": ["ctrl+alt+e"],
            "command": "open_dir",
            "args": {"dir": "$file_path", "file": "$file_name"}
        },
        {
            "keys": ["f5"],
            "command": "build",
            "args": {"variant": "pyflakes"}
        },
        {
            "keys": ["ctrl+0"],
            "command": "reset_font_size"
        },
        {
            "keys": ["f10"],
            "command": "insert_date"
        },
        {
            "keys": ["f8"],
            "command": "build",
            "args": { "variant": "refscan" }
        }

    ]

    existing_keymap = _load_json_or_empty(keymap_file_path)
    existing_keymap = _prune_maketool_bindings(
        existing_keymap,
        maketool_bindings
    )
    new_keymap = _upsert_keybindings(existing_keymap, maketool_bindings)    

    # _backup(keymap_file_path)

    with open(keymap_file_path, "w", encoding="utf-8") as f:
        json.dump(new_keymap, f, indent=4)
    print(f"Updated keymap: {keymap_file_path}")

    # Pythonw.sublime-build (kept as in your current file)
    build_file_path = os.path.join(user_packages_dir, "Pythonw.sublime-build")
    maketool_build_config = {
        "selector": "source.python",
        "shell": True,
        "working_dir": "${file_path}",
        "cmd": ["maketool-run", "$file"],
        "file_regex": "File \"(.*)\", line (.*)",
        "variants": [
            {
                "name": "build",
                "cmd": ["maketool-build", "${file}"],
                "shell": True
            },
            {
                "name": "clean",
                "cmd": ["maketool-clean"],
                "shell": True
            },
            {
                "name": "refscan",
                "cmd": ["maketool-refscan", "${file}"],
                "working_dir": "${file_path}",
                "shell": True
            },
            {
                "name": "pyflakes",
                "cmd": ["pyflakes", "${file}"],
                "file_regex": "^(.*?):(\\d+):(\\d+): ([^\\n]+)",
                "shell": True
            },
            {
                "name": "print",
                "command": "run_macro_file",
                "args": {"file": "Packages/User/print.sublime-macro"}
            }
        ]
    }

    # _backup(build_file_path)
    
    with open(build_file_path, "w", encoding="utf-8") as f:
        json.dump(maketool_build_config, f, indent=4)
    print(f"Updated build: {build_file_path}")


def main() -> None:

    print("maketool-sublime running...")

    parser = argparse.ArgumentParser(description="Install/Update Sublime Text integration for maketool.")
    parser.parse_args()  # no --path parameter by design

    user_packages_dir = _detect_user_packages_dir()
    print(f"Using Sublime User Packages dir: {user_packages_dir}")
    process(user_packages_dir)
    print("Sublime Text setup complete!")


if __name__ == "__main__":
    main()
