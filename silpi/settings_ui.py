# -*- coding: utf-8 -*-
"""Silpi settings window (tkinter), run on its own thread.

The main thread owns the Win32 hook and message loop, so this UI lives in a
daemon thread and is opened on demand through a thread-safe queue.
"""
from __future__ import annotations

import copy
import queue
import threading
import tkinter as tk
from tkinter import ttk

_SPECIAL_KEYS = {
    "Return": 0x0D, "KP_Enter": 0x0D, "Tab": 0x09, "space": 0x20,
    "Escape": 0x1B, "BackSpace": 0x08, "Delete": 0x2E, "Insert": 0x2D,
    "Home": 0x24, "End": 0x23, "Prior": 0x21, "Next": 0x22,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
    "minus": 0xBD, "equal": 0xBB, "bracketleft": 0xDB, "bracketright": 0xDD,
    "backslash": 0xDC, "semicolon": 0xBA, "apostrophe": 0xDE,
    "comma": 0xBC, "period": 0xBE, "slash": 0xBF, "grave": 0xC0,
}


def keysym_to_vk(keysym: str):
    if not keysym:
        return None
    if len(keysym) == 1 and keysym.isalnum():
        return ord(keysym.upper())
    if len(keysym) == 1:
        ch = keysym
        punct = {"-": 0xBD, "=": 0xBB, "[": 0xDB, "]": 0xDD, "\\": 0xDC,
                 ";": 0xBA, "'": 0xDE, ",": 0xBC, ".": 0xBE, "/": 0xBF, "`": 0xC0}
        if ch in punct:
            return punct[ch]
    if keysym.startswith("F") and keysym[1:].isdigit():
        n = int(keysym[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)
    return _SPECIAL_KEYS.get(keysym)


_HK_ORDER = [("toggle", "Enable / disable"),
             ("switch_language", "Switch Odia / English"),
             ("convert_now", "Convert now"),
             ("settings", "Open settings"),
             ("keyboard", "On-Screen Keyboard"),
             ("converter", "Font Converter")]


class HotkeyEntry(ttk.Entry):
    def __init__(self, master, hotkey, **kw):
        super().__init__(master, width=22, **kw)
        self.hotkey = dict(hotkey or {})
        self.bind("<KeyPress>", self._on_key)
        self._refresh()

    def _on_key(self, event):
        ks = event.keysym
        if ks in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                  "Alt_L", "Alt_R", "Win_L", "Win_R", "Super_L", "Super_R"):
            return "break"
        vk = keysym_to_vk(ks)
        if vk is None:
            return "break"
        self.hotkey = {
            "vk": vk,
            "ctrl": bool(event.state & 0x0004),
            "shift": bool(event.state & 0x0001),
            "alt": bool(event.state & 0x0008),
            "win": bool(event.state & 0x0040),
        }
        self._refresh()
        return "break"

    def _refresh(self):
        hk = self.hotkey
        parts = []
        if hk.get("ctrl"):
            parts.append("Ctrl")
        if hk.get("alt"):
            parts.append("Alt")
        if hk.get("shift"):
            parts.append("Shift")
        if hk.get("win"):
            parts.append("Win")
        vk = hk.get("vk")
        if vk:
            name = {0x0D: "Enter", 0x09: "Tab", 0x20: "Space", 0x1B: "Esc"}.get(vk)
            parts.append(name or (chr(vk) if 0x30 <= vk <= 0x5A else f"VK{vk:02X}"))
        text = "+".join(parts) if parts else ""
        self.delete(0, "end")
        self.insert(0, text)

    def get_hotkey(self):
        return dict(self.hotkey)


class SettingsWindow:
    def __init__(self, config, on_save):
        self.config = config
        self.on_save = on_save
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._root = None
        self._thread.start()

    def open(self):
        self._q.put("open")

    # --- worker thread -----------------------------------------------------
    def _run(self):
        self._root = tk.Tk()
        self._root.title("Silpi Settings")
        self._root.resizable(False, False)
        self._build(self._root)
        self._root.protocol("WM_DELETE_WINDOW", self._root.withdraw)
        self._root.withdraw()
        self._poll()
        self._root.mainloop()

    def _poll(self):
        try:
            while True:
                self._q.get_nowait()
                self._open_ui()
        except queue.Empty:
            pass
        self._root.after(150, self._poll)

    def _open_ui(self):
        self._load_into_widgets(copy.deepcopy(self.config))
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()

    # --- UI ----------------------------------------------------------------
    def _build(self, root):
        pad = {"padx": 8, "pady": 4}
        self.var_enabled = tk.BooleanVar()
        self.var_lang = tk.StringVar()
        self.var_scheme = tk.StringVar()
        self.var_notify = tk.BooleanVar()
        self.var_space = tk.BooleanVar()
        self.var_enter = tk.BooleanVar()
        self.var_tab = tk.BooleanVar()
        self.var_punct = tk.BooleanVar()

        frm = ttk.Frame(root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Checkbutton(frm, text="Enabled", variable=self.var_enabled).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(frm, text="Language").grid(row=1, column=0, sticky="w", **pad)
        lf = ttk.Frame(frm)
        lf.grid(row=1, column=1, sticky="w", **pad)
        ttk.Radiobutton(lf, text="Odia", variable=self.var_lang, value="or").pack(side="left")
        ttk.Radiobutton(lf, text="English", variable=self.var_lang, value="en").pack(side="left")

        ttk.Label(frm, text="Scheme").grid(row=2, column=0, sticky="w", **pad)
        sf = ttk.Frame(frm)
        sf.grid(row=2, column=1, sticky="w", **pad)
        ttk.Radiobutton(sf, text="Phonetic", variable=self.var_scheme, value="phonetic").pack(side="left")
        ttk.Radiobutton(sf, text="Akruti", variable=self.var_scheme, value="akruti").pack(side="left")

        ttk.Separator(frm, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Label(frm, text="Commit keys").grid(row=4, column=0, sticky="nw", **pad)
        cf = ttk.Frame(frm)
        cf.grid(row=4, column=1, sticky="w", **pad)
        ttk.Checkbutton(cf, text="Space", variable=self.var_space).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(cf, text="Enter", variable=self.var_enter).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(cf, text="Tab", variable=self.var_tab).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(cf, text="Punctuation", variable=self.var_punct).grid(row=1, column=1, sticky="w")

        ttk.Separator(frm, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Label(frm, text="Hotkeys").grid(row=6, column=0, sticky="nw", **pad)
        hf = ttk.Frame(frm)
        hf.grid(row=6, column=1, sticky="w", **pad)
        self.hk_entries = {}
        for i, (name, label) in enumerate(_HK_ORDER):
            ttk.Label(hf, text=label).grid(row=i, column=0, sticky="w", pady=2)
            e = HotkeyEntry(hf, self.config["hotkeys"].get(name, {}))
            e.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=2)
            self.hk_entries[name] = e

        ttk.Separator(frm, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Checkbutton(frm, text="Show tray notifications", variable=self.var_notify).grid(row=8, column=0, columnspan=2, sticky="w", **pad)

        # Creator Credentials / About
        about_frame = ttk.Frame(frm)
        about_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        lbl_brand = ttk.Label(
            about_frame,
            text="✨ Silpi – Universal Odia Typing Suite",
            font=("Segoe UI", 9, "bold")
        )
        lbl_brand.pack(anchor="w")
        lbl_cred = ttk.Label(
            about_frame,
            text="Crafted & Engineered with ❤️ by Aniket Nayak",
            font=("Segoe UI", 8, "italic")
        )
        lbl_cred.pack(anchor="w")

        bf = ttk.Frame(frm)
        bf.grid(row=10, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(bf, text="Cancel", command=self._root.withdraw).pack(side="right", padx=4)
        ttk.Button(bf, text="Save", command=self._save).pack(side="right")

    def _load_into_widgets(self, cfg):
        self._working = cfg
        self.var_enabled.set(bool(cfg.get("enabled")))
        self.var_lang.set(cfg.get("language", "or"))
        self.var_scheme.set(cfg.get("scheme", "phonetic"))
        self.var_notify.set(bool(cfg.get("tray_notifications")))
        self.var_space.set(bool(cfg.get("commit_space")))
        self.var_enter.set(bool(cfg.get("commit_enter")))
        self.var_tab.set(bool(cfg.get("commit_tab")))
        self.var_punct.set(bool(cfg.get("commit_punct")))
        for name, entry in self.hk_entries.items():
            entry.hotkey = dict(cfg["hotkeys"].get(name, {}))
            entry._refresh()

    def _save(self):
        cfg = self._working
        cfg["enabled"] = self.var_enabled.get()
        cfg["language"] = self.var_lang.get()
        cfg["scheme"] = self.var_scheme.get()
        cfg["tray_notifications"] = self.var_notify.get()
        cfg["commit_space"] = self.var_space.get()
        cfg["commit_enter"] = self.var_enter.get()
        cfg["commit_tab"] = self.var_tab.get()
        cfg["commit_punct"] = self.var_punct.get()
        cfg["hotkeys"] = {name: e.get_hotkey() for name, e in self.hk_entries.items()}
        self.on_save(cfg)
        self._root.withdraw()
