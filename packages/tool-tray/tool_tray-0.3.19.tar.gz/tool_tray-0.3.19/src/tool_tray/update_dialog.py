import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from tool_tray.config import load_config
from tool_tray.manifest import Manifest, fetch_manifest


class UpdateDialog:
    """Simple update dialog - just logs."""

    def __init__(
        self, tools: list[str], token: str, tool_info: dict[str, tuple[str, Manifest]]
    ) -> None:
        self.tools = tools
        self.token = token
        self.tool_info = tool_info
        self.cancelled = False

        self.root = tk.Tk()
        self.root.title("Updating")
        self.root.resizable(True, True)
        self.root.minsize(400, 250)

        window_width = 500
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Log text
        self.log_text = tk.Text(
            frame,
            wrap=tk.WORD,
            font=("Monaco", 10) if sys.platform == "darwin" else ("Consolas", 9),
            state=tk.DISABLED,
            background="#1e1e1e",
            foreground="#d4d4d4",
            borderwidth=0,
            highlightthickness=0,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.copy_btn = ttk.Button(btn_frame, text="Copy", command=self._on_copy)
        self.copy_btn.pack(side=tk.LEFT)

        self.action_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel)
        self.action_btn.pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _log_raw(self, message: str) -> None:
        """Log without timestamp."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_copy(self) -> None:
        content = self.log_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(f"```\n{content}\n```")

        original = self.copy_btn.cget("text")
        self.copy_btn.config(text="Copied!")
        self.root.after(1000, lambda: self.copy_btn.config(text=original))

    def _on_cancel(self) -> None:
        self.cancelled = True
        self.root.destroy()

    def _on_close(self) -> None:
        self.root.destroy()

    def _install(self, name: str) -> bool:
        info = self.tool_info.get(name)
        if not info:
            self.root.after(0, lambda: self._log("Tool not found"))
            return False

        repo, manifest = info

        if manifest.type == "uv":
            url = f"git+https://oauth2:{self.token}@github.com/{repo}"
            proc = subprocess.Popen(
                ["uv", "tool", "install", url, "--force"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Stream stderr (uv outputs progress here)
            if proc.stderr:
                for line in proc.stderr:
                    line = line.strip()
                    if line:
                        self.root.after(0, lambda ln=line: self._log_raw(ln))
            proc.wait()
            return proc.returncode == 0
        else:
            from tool_tray.updater import install_tool

            return install_tool(repo, manifest, self.token)

    def _run_updates(self) -> None:
        succeeded = 0
        failed = 0

        for name in self.tools:
            if self.cancelled:
                break

            self.root.after(0, lambda n=name: self._log(f"Installing {n}..."))

            if self._install(name):
                succeeded += 1
            else:
                failed += 1
                self.root.after(0, lambda n=name: self._log(f"{n} failed"))

        self.root.after(0, lambda: self._log(f"Done: {succeeded} ok, {failed} failed"))
        self.root.after(
            0, lambda: self.action_btn.config(text="Close", command=self._on_close)
        )

    def run(self) -> None:
        threading.Thread(target=self._run_updates, daemon=True).start()
        self.root.mainloop()


def main() -> None:
    tools = sys.argv[1:]
    if not tools:
        print("Usage: python -m tool_tray.update_dialog tool1 tool2 ...")
        sys.exit(1)

    config = load_config()
    if not config:
        print("No config found")
        sys.exit(1)

    token = config.get("token", "")
    repos = config.get("repos", [])

    tool_info: dict[str, tuple[str, Manifest]] = {}
    for repo in repos:
        manifest = fetch_manifest(repo, token)
        if manifest:
            tool_info[manifest.name] = (repo, manifest)

    valid_tools = [t for t in tools if t in tool_info]
    if not valid_tools:
        print("No valid tools to update")
        sys.exit(1)

    UpdateDialog(valid_tools, token, tool_info).run()


if __name__ == "__main__":
    main()
