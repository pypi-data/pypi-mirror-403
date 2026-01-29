import sys
import tkinter as tk
from tkinter import ttk

from tool_tray.logging import get_log_dir


class LogViewer:
    """Simple log viewer dialog."""

    def __init__(self) -> None:
        self.log_path = get_log_dir() / "tooltray.log"

        self.root = tk.Tk()
        self.root.title("Logs")
        self.root.resizable(True, True)
        self.root.minsize(400, 300)

        window_width = 600
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Log text - word wrap, no scrollbars (mouse wheel works)
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

        # 3 buttons: Copy All | Refresh | Clear
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.copy_btn = ttk.Button(btn_frame, text="Copy All", command=self._on_copy)
        self.copy_btn.pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="Refresh", command=self._load).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        ttk.Button(btn_frame, text="Clear", command=self._on_clear).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self._load()

    def _load(self) -> None:
        """Load log content from file."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)

        if self.log_path.exists():
            self.log_text.insert(tk.END, self.log_path.read_text())
            self.log_text.see(tk.END)
        else:
            self.log_text.insert(tk.END, "(no logs yet)")

        self.log_text.configure(state=tk.DISABLED)

    def _on_copy(self) -> None:
        """Copy logs wrapped in backticks for Teams."""
        content = self.log_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(f"```\n{content}\n```")

        original = self.copy_btn.cget("text")
        self.copy_btn.config(text="Copied!")
        self.root.after(1000, lambda: self.copy_btn.config(text=original))

    def _on_clear(self) -> None:
        """Clear the log file."""
        if self.log_path.exists():
            self.log_path.unlink()
        self._load()

    def run(self) -> None:
        self.root.mainloop()


def show_log_viewer() -> None:
    LogViewer().run()


def main() -> None:
    show_log_viewer()


if __name__ == "__main__":
    main()
