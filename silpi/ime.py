# -*- coding: utf-8 -*-
"""Silpi input engine: turns physical keystrokes into Odia Unicode.

Two schemes:

* ``phonetic`` - Roman keys are echoed as typed and a parallel buffer is
  tracked; on a commit key the buffer is converted with
  :func:`silpi.translit.phonetic` and the typed Roman is replaced in place.
* ``akruti``   - direct key -> glyph map (:mod:`silpi.akruti_layout`); each
  key is swallowed and the Odia glyph is injected immediately.

The engine is called from the low-level keyboard hook; ``handle`` returns
``True`` when the event must be swallowed.
"""
from __future__ import annotations

from . import win32util as w32
from .akruti_layout import KEYMAP
from .candidates import get_candidates
from .translit import phonetic as _phonetic

VK_LWIN, VK_RWIN = 0x5B, 0x5C
VK_LSHIFT, VK_RSHIFT = 0xA0, 0xA1
VK_LCONTROL, VK_RCONTROL = 0xA2, 0xA3
VK_LMENU, VK_RMENU = 0xA4, 0xA5
VK_SHIFT, VK_CONTROL, VK_MENU = 0x10, 0x11, 0x12


class ImeEngine:
    def __init__(self, config, on_action=None, candidate_ui=None):
        self.config = config
        self.on_action = on_action
        self.candidate_ui = candidate_ui
        self.buffer = ""
        self._consumed = set()
        self._current_candidates: list[str] = []
        self._selected_index = 0

    # --- helpers -----------------------------------------------------------
    def _modifiers(self):
        g = w32.GetAsyncKeyState
        ctrl = bool(g(VK_CONTROL) & 0x8000) or bool(g(VK_LCONTROL) & 0x8000) or bool(g(VK_RCONTROL) & 0x8000)
        alt = bool(g(VK_MENU) & 0x8000) or bool(g(VK_LMENU) & 0x8000) or bool(g(VK_RMENU) & 0x8000)
        shift = bool(g(VK_SHIFT) & 0x8000) or bool(g(VK_LSHIFT) & 0x8000) or bool(g(VK_RSHIFT) & 0x8000)
        win = bool(g(VK_LWIN) & 0x8000) or bool(g(VK_RWIN) & 0x8000)
        caps = bool(w32.GetKeyState(w32.VK_CAPITAL) & 1)
        return ctrl, alt, shift, win, caps

    def _match_hotkey(self, vk, ctrl, alt, shift, win):
        for name, hk in (self.config.get("hotkeys") or {}).items():
            if (hk.get("vk") == vk and bool(hk.get("ctrl")) == ctrl
                    and bool(hk.get("alt")) == alt and bool(hk.get("shift")) == shift
                    and bool(hk.get("win")) == win):
                return name
        return None

    def _active(self):
        return bool(self.config.get("enabled")) and self.config.get("language") != "en"

    # --- main entry --------------------------------------------------------
    def handle(self, ev) -> bool:
        if ev.injected:
            return False

        ctrl, alt, shift, win, caps = self._modifiers()

        if ev.keydown:
            hk = self._match_hotkey(ev.vk, ctrl, alt, shift, win)
            if hk:
                self._consumed.add(ev.vk)
                if self.on_action:
                    self.on_action(hk)
                return True
        else:
            if ev.vk in self._consumed:
                self._consumed.discard(ev.vk)
                return True
            return False

        if not self._active():
            self._clear_buffer()
            return False

        if ctrl or alt or win:
            self._clear_buffer()
            return False

        scheme = self.config.get("scheme")
        if scheme == "akruti":
            self._hide_candidates()
            return self._handle_akruti(ev, shift, caps)
        return self._handle_phonetic(ev, shift, caps)

    def _clear_buffer(self):
        self.buffer = ""
        self._hide_candidates()

    def _hide_candidates(self):
        self._current_candidates = []
        self._selected_index = 0
        if self.candidate_ui:
            self.candidate_ui.hide()

    def _update_candidates(self):
        if self.buffer:
            self._current_candidates = get_candidates(self.buffer, max_count=5)
            self._selected_index = 0
            if self.candidate_ui:
                self.candidate_ui.update_candidates(self._current_candidates, self._selected_index)
        else:
            self._hide_candidates()

    # --- akruti: direct map ------------------------------------------------
    def _handle_akruti(self, ev, shift, caps) -> bool:
        ch = w32.vk_to_char(ev.vk, shift, caps)
        if ch is not None and ch in KEYMAP:
            out = KEYMAP[ch]
            if out:
                w32.send_unicode(out)
                self._consumed.add(ev.vk)
                return True
        return False

    # --- phonetic: buffer + candidate prediction ---------------------------
    def _handle_phonetic(self, ev, shift, caps) -> bool:
        if ev.vk == w32.VK_BACK:
            if self.buffer:
                self.buffer = self.buffer[:-1]
                self._update_candidates()
            return False

        if ev.vk == w32.VK_ESCAPE:
            self._clear_buffer()
            return False

        # Selection of candidate via number keys (1 to 5)
        if self.buffer and not shift and 0x31 <= ev.vk <= 0x35:
            num_idx = ev.vk - 0x31
            if num_idx < len(self._current_candidates):
                selected_text = self._current_candidates[num_idx]
                return self._commit_chosen(ev, selected_text)

        ch = w32.vk_to_char(ev.vk, shift, caps)

        if ch is not None and ch.isalpha():
            self.buffer += ch
            self._update_candidates()
            return False

        boundary = ev.vk in (w32.VK_SPACE, w32.VK_RETURN, w32.VK_TAB) or (
            ch is not None and ch.isprintable())
        if not boundary:
            self._clear_buffer()
            return False

        if not self.buffer:
            return False

        if not self._commit_enabled(ev, ch):
            if ch is not None and ch.isprintable():
                self.buffer += ch
                self._update_candidates()
            else:
                self.buffer += " "
            return False

        chosen = self._current_candidates[0] if self._current_candidates else _phonetic(self.buffer)
        return self._commit_chosen(ev, chosen, append_char=ch)

    def _commit_enabled(self, ev, ch):
        if ev.vk == w32.VK_SPACE:
            return bool(self.config.get("commit_space"))
        if ev.vk == w32.VK_RETURN:
            return bool(self.config.get("commit_enter"))
        if ev.vk == w32.VK_TAB:
            return bool(self.config.get("commit_tab"))
        return bool(self.config.get("commit_punct"))

    def _commit_chosen(self, ev, chosen_text: str, append_char: str | None = None) -> bool:
        n = len(self.buffer)
        self.buffer = ""
        self._hide_candidates()
        w32.replace_backspaces_text(n, chosen_text)
        if ev.vk == w32.VK_SPACE:
            w32.send_unicode(" ")
        elif ev.vk == w32.VK_TAB:
            w32.send_key(w32.VK_TAB, False)
            w32.send_key(w32.VK_TAB, True)
        elif ev.vk == w32.VK_RETURN:
            w32.send_key(w32.VK_RETURN, False)
            w32.send_key(w32.VK_RETURN, True)
        elif append_char is not None and append_char != " " and not (0x31 <= ev.vk <= 0x35):
            w32.send_unicode(append_char)
        self._consumed.add(ev.vk)
        return True
