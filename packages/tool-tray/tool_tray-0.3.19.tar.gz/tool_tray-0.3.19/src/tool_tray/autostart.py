import subprocess
import sys
from pathlib import Path


def _get_tooltray_path() -> str | None:
    """Get the path to tooltray executable. Returns None if not found."""
    import shutil

    return shutil.which("tooltray")


def _linux_autostart_enable() -> bool:
    """Add tooltray to Linux autostart."""
    from tool_tray.logging import log_error, log_info

    exe = _get_tooltray_path()
    if not exe:
        log_error("Cannot enable autostart: tooltray not found in PATH")
        print("Error: tooltray not found in PATH")
        return False

    desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
    desktop_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        desktop_file.write_text(f"""[Desktop Entry]
Type=Application
Name=Tool Tray
Comment=System tray tool manager
Exec={exe}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
        log_info(f"Autostart enabled: {desktop_file}")
        print(f"Autostart enabled: {desktop_file}")
        return True
    except OSError as e:
        log_error(f"Failed to enable autostart: {desktop_file}", e)
        print(f"Failed to enable autostart: {e}")
        return False


def _linux_autostart_disable() -> bool:
    """Remove tooltray from Linux autostart."""
    from tool_tray.logging import log_info

    desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        log_info(f"Autostart disabled: {desktop_file}")
        print(f"Autostart disabled: {desktop_file}")
        return True
    print("Autostart was not enabled")
    return False


def _macos_autostart_enable() -> bool:
    """Add tooltray to macOS autostart via LaunchAgent."""
    import shutil

    from tool_tray.logging import log_error, log_info

    # Find both binaries - fail fast if either missing
    uv_bin = shutil.which("uv")
    tooltray_bin = shutil.which("tooltray")

    if not uv_bin:
        log_error("Cannot enable autostart: uv not found in PATH")
        print("Error: uv not found in PATH. Install uv first.")
        return False

    if not tooltray_bin:
        log_error("Cannot enable autostart: tooltray not found in PATH")
        print("Error: tooltray not found in PATH")
        return False

    # Collect unique directories for PATH
    path_dirs = {str(Path(uv_bin).parent), str(Path(tooltray_bin).parent)}
    path_env = ":".join(sorted(path_dirs)) + ":/usr/bin:/bin"

    # Get TCL_LIBRARY for tkinter to work under launchd
    import tkinter

    tcl_library = tkinter.Tcl().eval("info library")

    plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
    plist.parent.mkdir(parents=True, exist_ok=True)

    # Use sys.executable to run with same Python interpreter
    python_exe = sys.executable

    log_dir = Path.home() / "Library/Logs/tooltray"
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tooltray</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>-m</string>
        <string>tool_tray</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{path_env}</string>
        <key>TCL_LIBRARY</key>
        <string>{tcl_library}</string>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_dir}/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/stderr.log</string>
</dict>
</plist>""")
        subprocess.run(["launchctl", "load", str(plist)], check=False)
        log_info(f"Autostart enabled: {plist}")
        print(f"Autostart enabled: {plist}")
        return True
    except OSError as e:
        log_error(f"Failed to enable autostart: {plist}", e)
        print(f"Failed to enable autostart: {e}")
        return False


def _macos_autostart_disable() -> bool:
    """Remove tooltray from macOS autostart."""
    from tool_tray.logging import log_info

    plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
    if plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], check=False)
        plist.unlink()
        log_info(f"Autostart disabled: {plist}")
        print(f"Autostart disabled: {plist}")
        return True
    print("Autostart was not enabled")
    return False


def _windows_autostart_enable() -> bool:
    """Add tooltray to Windows autostart via registry."""
    from tool_tray.logging import log_error, log_info

    try:
        import winreg
    except ImportError:
        print("winreg not available (not Windows)")
        return False

    exe = _get_tooltray_path()
    if not exe:
        log_error("Cannot enable autostart: tooltray not found in PATH")
        print("Error: tooltray not found in PATH")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "ToolTray", 0, winreg.REG_SZ, exe)
        winreg.CloseKey(key)
        log_info("Autostart enabled via registry")
        print("Autostart enabled via registry")
        return True
    except OSError as e:
        log_error("Failed to enable autostart via registry", e)
        print(f"Failed to enable autostart: {e}")
        return False


def _windows_autostart_disable() -> bool:
    """Remove tooltray from Windows autostart."""
    from tool_tray.logging import log_info

    try:
        import winreg
    except ImportError:
        print("winreg not available (not Windows)")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, "ToolTray")
        winreg.CloseKey(key)
        log_info("Autostart disabled via registry")
        print("Autostart disabled")
        return True
    except FileNotFoundError:
        print("Autostart was not enabled")
        return False
    except OSError as e:
        print(f"Failed to disable autostart: {e}")
        return False


def enable_autostart() -> bool:
    """Add tooltray to system autostart."""
    from tool_tray.logging import log_debug

    log_debug(f"Enabling autostart on {sys.platform}")
    if sys.platform == "darwin":
        return _macos_autostart_enable()
    elif sys.platform == "win32":
        return _windows_autostart_enable()
    else:
        return _linux_autostart_enable()


def disable_autostart() -> bool:
    """Remove tooltray from system autostart."""
    from tool_tray.logging import log_debug

    log_debug(f"Disabling autostart on {sys.platform}")
    if sys.platform == "darwin":
        return _macos_autostart_disable()
    elif sys.platform == "win32":
        return _windows_autostart_disable()
    else:
        return _linux_autostart_disable()


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    if sys.platform == "darwin":
        plist = Path.home() / "Library/LaunchAgents/com.tooltray.plist"
        return plist.exists()
    elif sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, "ToolTray")
            winreg.CloseKey(key)
            return True
        except (ImportError, FileNotFoundError, OSError):
            return False
    else:
        desktop_file = Path.home() / ".config/autostart/tooltray.desktop"
        return desktop_file.exists()
