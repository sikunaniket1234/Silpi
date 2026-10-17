# -*- coding: utf-8 -*-
"""On-screen visual keyboard popup for Silpi.

Allows users to click or touch keys to type directly into any active Windows
application without taking input focus from that target window (WS_EX_NOACTIVATE).
Supports both Akruti and Phonetic schemes, Shift state toggle, and quick conjuncts.
"""
from __future__ import annotations

import ctypes
import queue
import threading
import tkinter as tk
from tkinter import ttk

from . import win32util as w32
from .akruti_layout import KEYMAP

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

# QWERTY Key Rows: (unshifted_key, shifted_key)
ROW_1 = [
    ("`", "~"), ("1", "!"), ("2", "@"), ("3", "#"), ("4", "$"),
    ("5", "%"), ("6", "^"), ("7", "&"), ("8", "*"), ("9", "("),
    ("0", ")"), ("-", "_"), ("=", "+"),
]
ROW_2 = [
    ("q", "Q"), ("w", "W"), ("e", "E"), ("r", "R"), ("t", "T"),
    ("y", "Y"), ("u", "U"), ("i", "I"), ("o", "O"), ("p", "P"),
    ("[", "{"), ("]", "}"), ("\\", "|"),
]
ROW_3 = [
    ("a", "A"), ("s", "S"), ("d", "D"), ("f", "F"), ("g", "G"),
    ("h", "H"), ("j", "J"), ("k", "K"), ("l", "L"), (";", ":"),
    ("'", '"'),
]
ROW_4 = [
    ("z", "Z"), ("x", "X"), ("c", "C"), ("v", "V"), ("b", "B"),
    ("n", "N"), ("m", "M"), (",", "<"), (".", ">"), ("/", "?"),
]

# Quick Conjuncts / Common Akruti Yuktakshara buttons
QUICK_CONJUNCTS = [
    ("କ୍ଷ", "#"), ("ଜ୍ଞ", "%"), ("ତ୍ର", "$"), ("ଶ୍ର", "@"),
    ("୍ର (ra-phala)", "^"), ("ର୍ (reph)", "&"), ("୍ୟ (ya-phala)", "Y"),
    ("୍ (halanta)", "f"), ("ା", "a"), ("ି", "i"), ("ୀ", "I"),
    ("ୁ", "u"), ("ୂ", "U"), ("ୃ", "="), ("େ", "e"), ("ୈ", "E"),
    ("ୋ", "o"), ("ୌ", "O"), ("ଂ", "x"), ("ଁ", "X"), ("ଃ", ":"),
]


class OnScreenKeyboardWindow:
    def __init__(self, config_provider, on_type=None):
        self.config_provider = config_provider
        self.on_type = on_type
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._root = None
        self._shift_active = False
        self._key_buttons = []
        self._thread.start()

    def open(self):
        self._q.put("open")

    def toggle(self):
        self._q.put("toggle")

    # --- worker thread -----------------------------------------------------
    def _run(self):
        self._root = tk.Tk()
        self._root.title("Silpi – Odia On-Screen Keyboard (ଅକ୍ଷର ପଟଳ)")
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)

        self._build_ui(self._root)

        # Set WS_EX_NOACTIVATE so clicking keys doesn't steal focus from MS Word / Notepad
        self._apply_noactivate()

        self._root.protocol("WM_DELETE_WINDOW", self._root.withdraw)
        self._root.withdraw()
        self._poll()
        self._root.mainloop()

    def _apply_noactivate(self):
        try:
            self._root.update_idletasks()
            hwnd = self._root.winfo_id()
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE | WS_EX_TOPMOST)
        except Exception:
            pass

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg == "open":
                    self._show_ui()
                elif msg == "toggle":
                    if self._root.state() == "normal":
                        self._root.withdraw()
                    else:
                        self._show_ui()
        except queue.Empty:
            pass
        self._root.after(150, self._poll)

    def _show_ui(self):
        self._refresh_keys()
        self._root.deiconify()
        self._apply_noactivate()

    # --- UI building -------------------------------------------------------
    def _build_ui(self, root):
        root.configure(bg="#202225")
        main_frame = tk.Frame(root, bg="#202225", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Title & instructions bar
        top_bar = tk.Frame(main_frame, bg="#202225")
        top_bar.pack(fill="x", pady=(0, 8))

        lbl_title = tk.Label(
            top_bar,
            text="ଓଡ଼ିଆ ଅକ୍ଷର ପଟଳ (Odia On-Screen Keyboard)",
            font=("Segoe UI", 11, "bold"),
            bg="#202225",
            fg="#58a6ff"
        )
        lbl_title.pack(side="left")

        lbl_credit = tk.Label(
            top_bar,
            text="• by Aniket Nayak",
            font=("Segoe UI", 9, "italic"),
            bg="#202225",
            fg="#e3b341"
        )
        lbl_credit.pack(side="left", padx=(6, 0))

        lbl_hint = tk.Label(
            top_bar,
            text="Click any key to type directly into active editor (Word, Notepad, Browser)",
            font=("Segoe UI", 8),
            bg="#202225",
            fg="#8b949e"
        )
        lbl_hint.pack(side="right")

        # Key rows container
        kb_container = tk.Frame(main_frame, bg="#202225")
        kb_container.pack(fill="x")

        self._build_row(kb_container, ROW_1, row_idx=0)
        self._build_row(kb_container, ROW_2, row_idx=1)
        self._build_row(kb_container, ROW_3, row_idx=2)
        self._build_row(kb_container, ROW_4, row_idx=3)

        # Space and Action Row
        ctrl_row = tk.Frame(main_frame, bg="#202225")
        ctrl_row.pack(fill="x", pady=(6, 4))

        self.btn_shift = tk.Button(
            ctrl_row,
            text="Shift [⇧]",
            font=("Segoe UI", 9, "bold"),
            width=10,
            bg="#30363d",
            fg="#f0f6fc",
            activebackground="#484f58",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            takefocus=0,
            command=self._toggle_shift
        )
        self.btn_shift.pack(side="left", padx=2)

        btn_space = tk.Button(
            ctrl_row,
            text="Space (ବ୍ୟବଧାନ)",
            font=("Segoe UI", 9),
            width=38,
            bg="#2b3137",
            fg="#f0f6fc",
            activebackground="#3b434b",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            takefocus=0,
            command=lambda: self._type_text(" ")
        )
        btn_space.pack(side="left", padx=4)

        btn_bs = tk.Button(
            ctrl_row,
            text="Backspace [⌫]",
            font=("Segoe UI", 9),
            width=12,
            bg="#442726",
            fg="#ff7b72",
            activebackground="#5c3332",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            takefocus=0,
            command=self._backspace
        )
        btn_bs.pack(side="left", padx=2)

        btn_enter = tk.Button(
            ctrl_row,
            text="Enter [↵]",
            font=("Segoe UI", 9),
            width=10,
            bg="#1f3b2b",
            fg="#7ee787",
            activebackground="#2b523c",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            takefocus=0,
            command=self._enter
        )
        btn_enter.pack(side="left", padx=2)

        # Quick Yuktakshara / Conjuncts bar
        conj_frame = tk.LabelFrame(
            main_frame,
            text="ଯୁକ୍ତାକ୍ଷର ଓ ମାତ୍ରା (Quick Conjuncts & Signs)",
            font=("Segoe UI", 8, "bold"),
            bg="#202225",
            fg="#8b949e",
            padx=4,
            pady=4
        )
        conj_frame.pack(fill="x", pady=(6, 2))

        for text, key_code in QUICK_CONJUNCTS:
            target_str = KEYMAP.get(key_code, text)
            btn = tk.Button(
                conj_frame,
                text=text,
                font=("Nirmala UI", 9, "bold"),
                bg="#21262d",
                fg="#79c0ff",
                activebackground="#30363d",
                activeforeground="#ffffff",
                relief="groove",
                bd=1,
                takefocus=0,
                command=lambda s=target_str: self._type_text(s)
            )
            btn.pack(side="left", padx=2, pady=1)

    def _build_row(self, parent, key_pairs, row_idx):
        row_frame = tk.Frame(parent, bg="#202225")
        row_frame.pack(fill="x", pady=2)

        for unshifted, shifted in key_pairs:
            btn = tk.Button(
                row_frame,
                font=("Nirmala UI", 10, "bold"),
                width=5,
                height=1,
                bg="#21262d",
                fg="#f0f6fc",
                activebackground="#388bfd",
                activeforeground="#ffffff",
                relief="raised",
                bd=1,
                takefocus=0
            )
            btn.pack(side="left", padx=2)
            self._key_buttons.append((btn, unshifted, shifted))
            btn.configure(command=lambda u=unshifted, s=shifted: self._on_key_click(u, s))

    def _refresh_keys(self):
        for btn, unshifted, shifted in self._key_buttons:
            active_char = shifted if self._shift_active else unshifted
            odia_char = KEYMAP.get(active_char, active_char)
            # Show Odia glyph prominent, with physical ASCII key below/beside
            label = f"{odia_char}\n{active_char}"
            btn.configure(text=label)
        if self._shift_active:
            self.btn_shift.configure(bg="#1f6feb", fg="#ffffff")
        else:
            self.btn_shift.configure(bg="#30363d", fg="#f0f6fc")

    def _toggle_shift(self):
        self._shift_active = not self._shift_active
        self._refresh_keys()

    def _on_key_click(self, unshifted, shifted):
        char = shifted if self._shift_active else unshifted
        out = KEYMAP.get(char, char)
        self._type_text(out)
        if self._shift_active:
            self._shift_active = False
            self._refresh_keys()

    def _type_text(self, text):
        w32.send_unicode(text)

    def _backspace(self):
        w32.send_backspaces(1)

    def _enter(self):
        w32.send_unicode("\n")
