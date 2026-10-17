# -*- coding: utf-8 -*-
"""Silpi application entry point.

Owns the low-level keyboard hook and the Win32 message loop on the main
thread, the tray icon, and the settings window thread.
"""
from __future__ import annotations

import ctypes
import os

from . import config as config_mod
from . import win32util as w32
from .ime import ImeEngine
from .candidate_ui import CandidatePopupWindow
from .converter_ui import FontConverterWindow
from .keyboard_ui import OnScreenKeyboardWindow
from .settings_ui import SettingsWindow

# tray command ids
CMD_TOGGLE = 100
CMD_LANG_OR = 201
CMD_LANG_EN = 202
CMD_SCHEME_PHONETIC = 301
CMD_SCHEME_AKRUTI = 302
CMD_KEYBOARD = 350
CMD_CONVERTER = 360
CMD_SETTINGS = 400
CMD_EXIT = 401

APP_TITLE = "Silpi"


def _asset(name: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", name)


def _acquire_single_instance(name: str = "Silpi_SingleInstance"):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
    handle = kernel32.CreateMutexW(None, 0, name)
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return handle


class SilpiApp:
    def __init__(self):
        self.config = config_mod.load()
        self.candidate_ui = CandidatePopupWindow(on_select=self._on_candidate_select)
        self.engine = ImeEngine(self.config, on_action=self._on_action, candidate_ui=self.candidate_ui)
        self.hook = None
        self.tray = None
        self.settings = SettingsWindow(self.config, on_save=self._on_settings_save)
        self.keyboard = OnScreenKeyboardWindow(self.config)
        self.converter = FontConverterWindow()

    def _on_candidate_select(self, text: str):
        if self.engine.buffer:
            n = len(self.engine.buffer)
            self.engine.buffer = ""
            self.candidate_ui.hide()
            w32.replace_backspaces_text(n, text)

    # --- lifecycle ---------------------------------------------------------
    def run(self):
        self.hook = w32.KeyboardHook(self.engine.handle)
        self.hook.install()
        self.tray = w32.TrayIcon(APP_TITLE, _asset("silpi.ico"),
                                 on_command=self._on_command,
                                 on_activate=self._toggle_enabled)
        self.tray.create()
        self.tray.set_menu_provider(self._build_menu)
        self._refresh_tooltip()
        try:
            w32.run_message_loop()
        finally:
            self._shutdown()

    def _shutdown(self):
        try:
            if self.tray:
                self.tray.destroy()
        finally:
            if self.hook:
                self.hook.uninstall()

    # --- tray menu ---------------------------------------------------------
    def _build_menu(self):
        cfg = self.config
        lang = cfg.get("language")
        scheme = cfg.get("scheme")
        return [
            ("item", CMD_TOGGLE, "Enabled", bool(cfg.get("enabled"))),
            ("sub", "Language", [
                ("item", CMD_LANG_OR, "Odia (\u0b13\u0b21\u0b3c\u0b3f\u0b06)", lang == "or"),
                ("item", CMD_LANG_EN, "English", lang == "en"),
            ]),
            ("sub", "Scheme", [
                ("item", CMD_SCHEME_PHONETIC, "Phonetic", scheme == "phonetic"),
                ("item", CMD_SCHEME_AKRUTI, "Akruti", scheme == "akruti"),
            ]),
            ("sep",),
            ("item", CMD_KEYBOARD, "On-Screen Keyboard (ଅକ୍ଷର ପଟଳ)\u2026", None),
            ("item", CMD_CONVERTER, "Font Converter (ଫଣ୍ଟ ରୂପାନ୍ତରଣ)\u2026", None),
            ("item", CMD_SETTINGS, "Settings\u2026", None),
            ("sep",),
            ("item", CMD_EXIT, "Exit", None),
        ]

    def _on_command(self, cid):
        if cid == CMD_TOGGLE:
            self._toggle_enabled()
        elif cid == CMD_LANG_OR:
            self._set(language="or")
        elif cid == CMD_LANG_EN:
            self._set(language="en")
        elif cid == CMD_SCHEME_PHONETIC:
            self._set(scheme="phonetic")
        elif cid == CMD_SCHEME_AKRUTI:
            self._set(scheme="akruti")
        elif cid == CMD_KEYBOARD:
            self.keyboard.open()
        elif cid == CMD_CONVERTER:
            self.converter.open()
        elif cid == CMD_SETTINGS:
            self.settings.open()
        elif cid == CMD_EXIT:
            self._exit()

    def _on_action(self, name):
        if name == "toggle":
            self._toggle_enabled()
        elif name == "switch_language":
            self._set(language="en" if self.config.get("language") == "or" else "or")
        elif name == "convert_now":
            self.engine.buffer = ""
        elif name == "keyboard":
            self.keyboard.toggle()
        elif name == "converter":
            self.converter.toggle()
        elif name == "settings":
            self.settings.open()

    # --- state changes -----------------------------------------------------
    def _toggle_enabled(self):
        self._set(enabled=not self.config.get("enabled"))

    def _set(self, **kwargs):
        self.config.update(kwargs)
        config_mod.save(self.config)
        self._refresh_tooltip()
        self._notify()

    def _on_settings_save(self, cfg):
        self.config.clear()
        self.config.update(cfg)
        config_mod.save(self.config)
        self._refresh_tooltip()

    def _refresh_tooltip(self):
        if not self.tray:
            return
        cfg = self.config
        if not cfg.get("enabled"):
            state = "Off"
        elif cfg.get("language") == "en":
            state = "English"
        else:
            state = "Odia \u2013 " + cfg.get("scheme", "phonetic").capitalize()
        self.tray.set_tooltip(f"Silpi \u2013 {state}")

    def _notify(self):
        if not (self.tray and self.config.get("tray_notifications")):
            return
        if not self.config.get("enabled"):
            self.tray.balloon(APP_TITLE, "Input disabled")
        elif self.config.get("language") == "en":
            self.tray.balloon(APP_TITLE, "English")
        else:
            self.tray.balloon(APP_TITLE, self._build_state_text())

    def _build_state_text(self):
        return f"Odia \u2013 {self.config.get('scheme', 'phonetic').capitalize()}"

    def _exit(self):
        if self.tray:
            self.tray.destroy()
            self.tray = None
        if self.hook:
            self.hook.uninstall()
            self.hook = None
        if self.tray is None:
            w32.PostQuitMessage(0)


def main():
    if _acquire_single_instance() is None:
        return
    app = SilpiApp()
    app.run()


if __name__ == "__main__":
    main()
