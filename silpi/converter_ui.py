# -*- coding: utf-8 -*-
"""Built-in legacy font / encoding converter window for Silpi.

Converts legacy non-Unicode fonts (such as Akruti, AkrutiOriSarala,
AkrutiOriSarala99, and ShreeLipi) to standard Odia Unicode, and vice-versa.
Runs in a separate thread so it does not block the Win32 hook loop.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk

from . import akruti_map


class FontConverterWindow:
    def __init__(self):
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._root = None
        self._thread.start()

    def open(self):
        self._q.put("open")

    def toggle(self):
        self._q.put("toggle")

    # --- worker thread -----------------------------------------------------
    def _run(self):
        self._root = tk.Tk()
        self._root.title("Silpi – Odia Font & Legacy Encoding Converter (ଫଣ୍ଟ ରୂପାନ୍ତରଣ)")
        self._root.geometry("820x540")
        self._root.minsize(680, 440)
        self._root.configure(bg="#181a1f")

        self._build_ui(self._root)

        self._root.protocol("WM_DELETE_WINDOW", self._root.withdraw)
        self._root.withdraw()
        self._poll()
        self._root.mainloop()

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg == "open":
                    self._root.deiconify()
                    self._root.lift()
                    self._root.focus_force()
                elif msg == "toggle":
                    if self._root.state() == "normal":
                        self._root.withdraw()
                    else:
                        self._root.deiconify()
                        self._root.lift()
                        self._root.focus_force()
        except queue.Empty:
            pass
        self._root.after(150, self._poll)

    # --- UI building -------------------------------------------------------
    def _build_ui(self, root):
        main_frame = tk.Frame(root, bg="#181a1f", padx=12, pady=12)
        main_frame.pack(fill="both", expand=True)

        # Header bar
        hdr = tk.Frame(main_frame, bg="#181a1f")
        hdr.pack(fill="x", pady=(0, 10))

        lbl_title = tk.Label(
            hdr,
            text="✨ Silpi – Odia Legacy Font Converter (ଫଣ୍ଟ ରୂପାନ୍ତରଣ)",
            font=("Segoe UI", 12, "bold"),
            bg="#181a1f",
            fg="#58a6ff"
        )
        lbl_title.pack(side="left")

        lbl_author = tk.Label(
            hdr,
            text="Crafted by Aniket Nayak",
            font=("Segoe UI", 9, "italic"),
            bg="#181a1f",
            fg="#e3b341"
        )
        lbl_author.pack(side="right")

        # Conversion direction controls
        ctrl_frame = tk.Frame(main_frame, bg="#21262d", padx=10, pady=8, bd=1, relief="ridge")
        ctrl_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            ctrl_frame,
            text="Conversion Mode:",
            font=("Segoe UI", 9, "bold"),
            bg="#21262d",
            fg="#f0f6fc"
        ).pack(side="left", padx=(0, 8))

        self.var_mode = tk.StringVar(value="akruti_to_unicode")
        modes = [
            ("Akruti / Sarala ➔ Odia Unicode", "akruti_to_unicode"),
            ("ShreeLipi ➔ Odia Unicode", "shree_to_unicode"),
        ]
        for text, val in modes:
            rb = tk.Radiobutton(
                ctrl_frame,
                text=text,
                value=val,
                variable=self.var_mode,
                font=("Segoe UI", 9),
                bg="#21262d",
                fg="#f0f6fc",
                selectcolor="#30363d",
                activebackground="#21262d",
                activeforeground="#58a6ff"
            )
            rb.pack(side="left", padx=8)

        # Split panes: Source & Result
        panes = tk.Frame(main_frame, bg="#181a1f")
        panes.pack(fill="both", expand=True)

        # Left: Source
        left_box = tk.LabelFrame(
            panes,
            text=" Source Text (Legacy Font / ASCII Input) ",
            font=("Segoe UI", 9, "bold"),
            bg="#181a1f",
            fg="#8b949e",
            padx=6,
            pady=6
        )
        left_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.txt_source = tk.Text(
            left_box,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#f0f6fc",
            insertbackground="#58a6ff",
            relief="flat",
            wrap="word",
            undo=True
        )
        self.txt_source.pack(fill="both", expand=True)

        # Right: Target
        right_box = tk.LabelFrame(
            panes,
            text=" Converted Output (Standard Odia Unicode) ",
            font=("Segoe UI", 9, "bold"),
            bg="#181a1f",
            fg="#7ee787",
            padx=6,
            pady=6
        )
        right_box.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.txt_target = tk.Text(
            right_box,
            font=("Nirmala UI", 11),
            bg="#0d1117",
            fg="#f0f6fc",
            insertbackground="#7ee787",
            relief="flat",
            wrap="word",
            undo=True
        )
        self.txt_target.pack(fill="both", expand=True)

        # Action bar at bottom
        action_bar = tk.Frame(main_frame, bg="#181a1f")
        action_bar.pack(fill="x", pady=(10, 0))

        self.lbl_status = tk.Label(
            action_bar,
            text="Ready. Paste text on the left and click 'Convert'.",
            font=("Segoe UI", 8),
            bg="#181a1f",
            fg="#8b949e"
        )
        self.lbl_status.pack(side="left")

        btn_clear = tk.Button(
            action_bar,
            text="Clear",
            font=("Segoe UI", 9),
            bg="#30363d",
            fg="#f0f6fc",
            activebackground="#484f58",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            padx=10,
            command=self._clear
        )
        btn_clear.pack(side="right", padx=(6, 0))

        btn_copy = tk.Button(
            action_bar,
            text="Copy Unicode Output",
            font=("Segoe UI", 9, "bold"),
            bg="#238636",
            fg="#ffffff",
            activebackground="#2ea043",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            padx=12,
            command=self._copy_output
        )
        btn_copy.pack(side="right", padx=(6, 0))

        btn_convert = tk.Button(
            action_bar,
            text="⚡ Convert to Unicode",
            font=("Segoe UI", 9, "bold"),
            bg="#1f6feb",
            fg="#ffffff",
            activebackground="#388bfd",
            activeforeground="#ffffff",
            relief="raised",
            bd=1,
            padx=14,
            command=self._convert
        )
        btn_convert.pack(side="right")

    def _convert(self):
        raw = self.txt_source.get("1.0", "end-1c")
        if not raw.strip():
            self.lbl_status.configure(text="Source text is empty.", fg="#e3b341")
            return

        converted = akruti_map.to_unicode(raw)
        self.txt_target.delete("1.0", "end")
        self.txt_target.insert("1.0", converted)
        self.lbl_status.configure(
            text=f"Converted {len(raw)} characters successfully to Unicode.",
            fg="#7ee787"
        )

    def _copy_output(self):
        out = self.txt_target.get("1.0", "end-1c")
        if out:
            self._root.clipboard_clear()
            self._root.clipboard_append(out)
            self.lbl_status.configure(text="Copied converted Unicode text to clipboard!", fg="#58a6ff")

    def _clear(self):
        self.txt_source.delete("1.0", "end")
        self.txt_target.delete("1.0", "end")
        self.lbl_status.configure(text="Cleared.", fg="#8b949e")
