# -*- coding: utf-8 -*-
"""Floating candidate popup window for word prediction / autosuggestions.

Displays a compact, modern horizontal candidate box near the active caret:
[ 1. ଭରତ  2. ଭାରତ  3. ଭାରତୀ  4. ଭାରତୀୟ  5. bharat ]
Does not steal focus (WS_EX_NOACTIVATE | WS_EX_TOPMOST).
"""
from __future__ import annotations

import ctypes
import queue
import threading
import tkinter as tk

from . import win32util as w32

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080


class CandidatePopupWindow:
    def __init__(self, on_select=None):
        self.on_select = on_select
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._root = None
        self._candidates: list[str] = []
        self._selected_index = 0
        self._labels: list[tk.Label] = []
        self._thread.start()

    def update_candidates(self, candidates: list[str], selected_index: int = 0):
        pos = w32.get_caret_or_cursor_pos()
        self._q.put(("update", candidates, selected_index, pos))

    def hide(self):
        self._q.put(("hide",))

    # --- worker thread -----------------------------------------------------
    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.configure(bg="#1e1e24", bd=1, relief="solid")

        self.container = tk.Frame(self._root, bg="#1e1e24", padx=6, pady=4)
        self.container.pack()

        self._apply_noactivate()
        self._root.withdraw()
        self._poll()
        self._root.mainloop()

    def _apply_noactivate(self):
        try:
            self._root.update_idletasks()
            hwnd = self._root.winfo_id()
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
            )
        except Exception:
            pass

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "update":
                    _, candidates, sel_idx, pos = msg
                    self._show_candidates(candidates, sel_idx, pos)
                elif msg[0] == "hide":
                    self._root.withdraw()
        except queue.Empty:
            pass
        self._root.after(50, self._poll)

    def _show_candidates(self, candidates: list[str], sel_idx: int, pos: tuple[int, int]):
        if not candidates:
            self._root.withdraw()
            return

        self._candidates = candidates
        self._selected_index = sel_idx

        # Clear existing labels
        for w in self.container.winfo_children():
            w.destroy()

        self._labels.clear()

        # Render candidates
        for idx, word in enumerate(candidates):
            is_active = (idx == sel_idx)
            bg_col = "#2a3b5c" if is_active else "#1e1e24"
            fg_col = "#58a6ff" if is_active else "#e6edf3"
            bd_col = "#388bfd" if is_active else "#1e1e24"

            item_frame = tk.Frame(self.container, bg=bg_col, padx=5, pady=2, bd=1, relief="solid", highlightbackground=bd_col)
            item_frame.pack(side="left", padx=2)

            num_lbl = tk.Label(item_frame, text=f"{idx + 1}.", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg=bg_col)
            num_lbl.pack(side="left")

            word_lbl = tk.Label(item_frame, text=f" {word}", font=("Nirmala UI", 11, "bold" if is_active else "normal"), fg=fg_col, bg=bg_col)
            word_lbl.pack(side="left")

            # Click selection support
            for widget in (item_frame, num_lbl, word_lbl):
                widget.bind("<Button-1>", lambda e, i=idx: self._on_click_select(i))

        x, y = pos
        self._root.geometry(f"+{x}+{y}")
        self._root.deiconify()
        self._root.lift()
        self._apply_noactivate()

    def _on_click_select(self, index: int):
        if self.on_select and 0 <= index < len(self._candidates):
            self.on_select(self._candidates[index])
        self._root.withdraw()
