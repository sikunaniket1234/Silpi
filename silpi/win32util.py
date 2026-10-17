# -*- coding: utf-8 -*-
"""Win32 utilities for Silpi: low-level keyboard hook, SendInput, tray icon.

Stdlib-only (ctypes). The caller drives the message loop.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
from ctypes import WINFUNCTYPE, Structure, Union, POINTER, byref

# --- Constants ---
WH_KEYBOARD_LL = 13
HC_ACTION = 0
LLKHF_INJECTED = 0x10

WM_NULL = 0
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 1
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205

NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 1, 2, 4, 0x10

TPM_RETURNCMD, TPM_RIGHTBUTTON, TPM_LEFTALIGN = 0x0100, 0x0002, 0
TPM_BOTTOMALIGN = 0x0020

IMAGE_ICON, LR_LOADFROMFILE, LR_DEFAULTSIZE = 1, 0x10, 0x40
IDI_APPLICATION = 32512

MF_STRING, MF_POPUP, MF_SEPARATOR = 0, 0x10, 0x800
MF_CHECKED, MF_UNCHECKED, MF_GRAYED = 8, 0, 1

VK_BACK, VK_TAB, VK_RETURN, VK_SPACE = 0x08, 0x09, 0x0D, 0x20
VK_CAPITAL, VK_SHIFT, VK_CONTROL, VK_MENU, VK_ESCAPE = 0x14, 0x10, 0x11, 0x12, 0x1B

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 1, 2
KEYEVENTF_UNICODE, KEYEVENTF_SCANCODE = 4, 8

HWND_MESSAGE = wt.HWND(-3)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)

MAGIC = 0x53494C50  # 'SILP'

ULONG_PTR = ctypes.c_size_t


class GUID(Structure):
    _fields_ = [("Data1", wt.DWORD), ("Data2", wt.WORD), ("Data3", wt.WORD),
                ("Data4", ctypes.c_ubyte * 8)]


# --- Structures ---
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

class KEYBDINPUT(Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

class MOUSEINPUT(Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

class HARDWAREINPUT(Structure):
    _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]

class INPUTUNION(Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(Structure):
    _fields_ = [("type", wt.DWORD), ("u", INPUTUNION)]

class POINT(Structure):
    _fields_ = [("x", wt.LONG), ("y", wt.LONG)]

class MSG(Structure):
    _fields_ = [("hwnd", wt.HWND), ("message", wt.UINT), ("wParam", wt.WPARAM),
                ("lParam", wt.LPARAM), ("time", wt.DWORD), ("pt", POINT)]

WNDPROC = WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
HOOKPROC = WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)

class WNDCLASSEXW(Structure):
    _fields_ = [("cbSize", wt.UINT), ("style", wt.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON), ("hCursor", wt.HCURSOR),
                ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                ("lpszClassName", wt.LPCWSTR), ("hIconSm", wt.HICON)]

class NOTIFYICONDATAW(Structure):
    _fields_ = [("cbSize", wt.DWORD), ("hWnd", wt.HWND), ("uID", wt.UINT),
                ("uFlags", wt.UINT), ("uCallbackMessage", wt.UINT), ("hIcon", wt.HICON),
                ("szTip", wt.WCHAR * 128), ("dwState", wt.DWORD), ("dwStateMask", wt.DWORD),
                ("szInfo", wt.WCHAR * 256), ("uVersion", wt.UINT),
                ("szInfoTitle", wt.WCHAR * 64), ("dwInfoFlags", wt.DWORD),
                ("guidItem", GUID), ("hBalloonIcon", wt.HICON)]

# --- Prototypes ---
SetWindowsHookExW = user32.SetWindowsHookExW
SetWindowsHookExW.restype = wt.HHOOK
SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD)
UnhookWindowsHookEx = user32.UnhookWindowsHookEx
UnhookWindowsHookEx.restype = wt.BOOL
UnhookWindowsHookEx.argtypes = (wt.HHOOK,)
CallNextHookEx = user32.CallNextHookEx
CallNextHookEx.restype = ctypes.c_ssize_t
CallNextHookEx.argtypes = (wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM)

GetModuleHandleW = kernel32.GetModuleHandleW
GetModuleHandleW.restype = wt.HINSTANCE
GetModuleHandleW.argtypes = (wt.LPCWSTR,)
DefWindowProcW = user32.DefWindowProcW
DefWindowProcW.restype = ctypes.c_ssize_t
DefWindowProcW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
RegisterClassExW = user32.RegisterClassExW
RegisterClassExW.restype = wt.ATOM
RegisterClassExW.argtypes = (POINTER(WNDCLASSEXW),)
CreateWindowExW = user32.CreateWindowExW
CreateWindowExW.restype = wt.HWND
CreateWindowExW.argtypes = (wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int,
                            ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU,
                            wt.HINSTANCE, wt.LPVOID)
GetMessageW = user32.GetMessageW
GetMessageW.restype = wt.BOOL
GetMessageW.argtypes = (POINTER(MSG), wt.HWND, wt.UINT, wt.UINT)
TranslateMessage = user32.TranslateMessage
TranslateMessage.restype = wt.BOOL
TranslateMessage.argtypes = (POINTER(MSG),)
DispatchMessageW = user32.DispatchMessageW
DispatchMessageW.restype = ctypes.c_ssize_t
DispatchMessageW.argtypes = (POINTER(MSG),)
PostQuitMessage = user32.PostQuitMessage
PostQuitMessage.restype = None
PostQuitMessage.argtypes = (ctypes.c_int,)
PostMessageW = user32.PostMessageW
PostMessageW.restype = wt.BOOL
PostMessageW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
SendInput = user32.SendInput
SendInput.restype = wt.UINT
SendInput.argtypes = (wt.UINT, POINTER(INPUT), ctypes.c_int)
CreatePopupMenu = user32.CreatePopupMenu
CreatePopupMenu.restype = wt.HMENU
AppendMenuW = user32.AppendMenuW
AppendMenuW.restype = wt.BOOL
AppendMenuW.argtypes = (wt.HMENU, wt.UINT, wt.UINT, wt.LPCWSTR)
DestroyMenu = user32.DestroyMenu
DestroyMenu.restype = wt.BOOL
DestroyMenu.argtypes = (wt.HMENU,)
TrackPopupMenu = user32.TrackPopupMenu
TrackPopupMenu.restype = wt.BOOL
TrackPopupMenu.argtypes = (wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, wt.HWND, POINTER(ctypes.c_void_p))
GetCursorPos = user32.GetCursorPos
GetCursorPos.restype = wt.BOOL
GetCursorPos.argtypes = (POINTER(POINT),)
SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.restype = wt.BOOL
SetForegroundWindow.argtypes = (wt.HWND,)
Shell_NotifyIconW = shell32.Shell_NotifyIconW
Shell_NotifyIconW.restype = wt.BOOL
Shell_NotifyIconW.argtypes = (wt.DWORD, POINTER(NOTIFYICONDATAW))
LoadImageW = user32.LoadImageW
LoadImageW.restype = wt.HANDLE
LoadImageW.argtypes = (wt.HINSTANCE, wt.LPCWSTR, wt.UINT, ctypes.c_int, ctypes.c_int, wt.UINT)
LoadIconW = user32.LoadIconW
LoadIconW.restype = wt.HICON
LoadIconW.argtypes = (wt.HINSTANCE, wt.LPCWSTR)
GetKeyState = user32.GetKeyState
GetKeyState.restype = wt.SHORT
GetKeyState.argtypes = (ctypes.c_int,)
GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.restype = wt.SHORT
GetAsyncKeyState.argtypes = (ctypes.c_int,)


# --- text / key injection ---
def _kbd_input(vk=0, scan=0, flags=0, extra=MAGIC):
    ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=extra)
    return INPUT(type=INPUT_KEYBOARD, u=INPUTUNION(ki=ki))


def send_key(vk, up=False, extra=MAGIC):
    flags = KEYEVENTF_KEYUP if up else 0
    inp = _kbd_input(vk=vk, flags=flags, extra=extra)
    SendInput(1, byref(inp), ctypes.sizeof(INPUT))


def send_unicode(text, extra=MAGIC):
    """Send text as Unicode key events (layout independent)."""
    units = text.encode("utf-16-le")
    for i in range(0, len(units), 2):
        cu = units[i] | (units[i + 1] << 8)
        inp = (_kbd_input(scan=cu, flags=KEYEVENTF_UNICODE, extra=extra),
               _kbd_input(scan=cu, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, extra=extra))
        SendInput(2, (INPUT * 2)(*inp), ctypes.sizeof(INPUT))


def send_backspaces(n, extra=MAGIC):
    for _ in range(max(0, n)):
        send_key(VK_BACK, False, extra)
        send_key(VK_BACK, True, extra)


def replace_backspaces_text(n, text, extra=MAGIC):
    """Delete ``n`` characters then type ``text`` in one batched SendInput."""
    arr = []
    for _ in range(max(0, n)):
        arr.append(_kbd_input(vk=VK_BACK, extra=extra))
        arr.append(_kbd_input(vk=VK_BACK, flags=KEYEVENTF_KEYUP, extra=extra))
    units = text.encode("utf-16-le")
    for i in range(0, len(units), 2):
        cu = units[i] | (units[i + 1] << 8)
        arr.append(_kbd_input(scan=cu, flags=KEYEVENTF_UNICODE, extra=extra))
        arr.append(_kbd_input(scan=cu, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, extra=extra))
    if arr:
        SendInput(len(arr), (INPUT * len(arr))(*arr), ctypes.sizeof(INPUT))


_VK_CHARS = {
    0x30: ("0", ")"), 0x31: ("1", "!"), 0x32: ("2", "@"), 0x33: ("3", "#"),
    0x34: ("4", "$"), 0x35: ("5", "%"), 0x36: ("6", "^"), 0x37: ("7", "&"),
    0x38: ("8", "*"), 0x39: ("9", "("), 0xBA: (";", ":"), 0xBB: ("=", "+"),
    0xBC: (",", "<"), 0xBD: ("-", "_"), 0xBE: (".", ">"), 0xBF: ("/", "?"),
    0xC0: ("`", "~"), 0xDB: ("[", "{"), 0xDC: ("\\", "|"), 0xDD: ("]", "}"),
    0xDE: ("'", '"'),
}


def vk_to_char(vk, shift=False, caps=False):
    if 0x41 <= vk <= 0x5A:
        ch = chr(vk)
        return ch.upper() if (shift ^ caps) else ch.lower()
    if vk in _VK_CHARS:
        low, high = _VK_CHARS[vk]
        return high if shift else low
    if vk == VK_SPACE:
        return " "
    return None


class RECT(Structure):
    _fields_ = [("left", wt.LONG), ("top", wt.LONG), ("right", wt.LONG), ("bottom", wt.LONG)]


class GUITHREADINFO(Structure):
    _fields_ = [
        ("cbSize", wt.DWORD),
        ("flags", wt.DWORD),
        ("hwndActive", wt.HWND),
        ("hwndFocus", wt.HWND),
        ("hwndCapture", wt.HWND),
        ("hwndMenuOwner", wt.HWND),
        ("hwndMoveSize", wt.HWND),
        ("hwndCaret", wt.HWND),
        ("rcCaret", RECT),
    ]


GetGUIThreadInfo = user32.GetGUIThreadInfo
GetGUIThreadInfo.restype = wt.BOOL
GetGUIThreadInfo.argtypes = (wt.DWORD, POINTER(GUITHREADINFO))
ClientToScreen = user32.ClientToScreen
ClientToScreen.restype = wt.BOOL
ClientToScreen.argtypes = (wt.HWND, POINTER(POINT))


def get_caret_or_cursor_pos() -> tuple[int, int]:
    """Return (x, y) screen coordinates of the active text caret or mouse cursor fallback."""
    gui = GUITHREADINFO()
    gui.cbSize = ctypes.sizeof(GUITHREADINFO)
    if GetGUIThreadInfo(0, byref(gui)) and gui.hwndCaret:
        pt = POINT(gui.rcCaret.left, gui.rcCaret.bottom + 4)
        ClientToScreen(gui.hwndCaret, byref(pt))
        if pt.x > 0 and pt.y > 0:
            return pt.x, pt.y

    # Fallback to mouse cursor position
    pt = POINT()
    if GetCursorPos(byref(pt)):
        return pt.x + 10, pt.y + 20
    return 200, 200


# --- keyboard hook ---
class KeyboardEvent:
    __slots__ = ("vk", "scan", "flags", "time", "injected", "keydown")

    def __init__(self, vk, scan, flags, time, injected, keydown):
        self.vk = vk
        self.scan = scan
        self.flags = flags
        self.time = time
        self.injected = injected
        self.keydown = keydown

    @property
    def keyup(self):
        return not self.keydown


class KeyboardHook:
    def __init__(self, handler):
        self._handler = handler
        self._hook = None
        self._cb = None

    def install(self):
        if self._hook:
            return
        self._cb = HOOKPROC(self._lowlevel)
        hmod = GetModuleHandleW(None)
        self._hook = SetWindowsHookExW(WH_KEYBOARD_LL, self._cb, hmod, 0)
        if not self._hook:
            raise ctypes.WinError(ctypes.get_last_error())

    def uninstall(self):
        if self._hook:
            UnhookWindowsHookEx(self._hook)
            self._hook = None
            self._cb = None

    def _lowlevel(self, ncode, wparam, lparam):
        if ncode == HC_ACTION:
            p = ctypes.cast(lparam, POINTER(KBDLLHOOKSTRUCT)).contents
            injected = bool(p.flags & LLKHF_INJECTED) or int(p.dwExtraInfo) == MAGIC
            keydown = wparam in (0x0100, 0x0104)
            ev = KeyboardEvent(p.vkCode, p.scanCode, p.flags, p.time, injected, keydown)
            try:
                if self._handler(ev):
                    return 1
            except Exception:
                pass
        return CallNextHookEx(self._hook, ncode, wparam, lparam)


def run_message_loop():
    msg = MSG()
    while GetMessageW(byref(msg), None, 0, 0) > 0:
        TranslateMessage(byref(msg))
        DispatchMessageW(byref(msg))
    return msg.wParam


# --- tray icon ---
class TrayIcon:
    """Message-only window owning a Shell_NotifyIcon tray icon."""

    def __init__(self, tooltip, icon_path, on_command, on_activate=None):
        self.tooltip = tooltip
        self.icon_path = icon_path
        self.on_command = on_command
        self.on_activate = on_activate
        self.hwnd = None
        self.hicon = None
        self._wndproc = None
        self._nid = NOTIFYICONDATAW()
        self._class_name = "SilpiTrayWnd"
        self._menu_provider = None

    def create(self):
        hinst = GetModuleHandleW(None)
        self._wndproc = WNDPROC(self._wnd_proc)
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinst
        wc.lpszClassName = self._class_name
        RegisterClassExW(byref(wc))
        self.hwnd = CreateWindowExW(0, self._class_name, "Silpi", 0, 0, 0, 0, 0,
                                    HWND_MESSAGE, None, hinst, None)
        if not self.hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        if self.icon_path and os.path.exists(self.icon_path):
            self.hicon = LoadImageW(None, str(self.icon_path), IMAGE_ICON, 0, 0,
                                    LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not self.hicon:
            self.hicon = LoadIconW(None, wt.LPCWSTR(IDI_APPLICATION))
        nid = self._nid
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self.hicon
        nid.szTip = self.tooltip[:127]
        Shell_NotifyIconW(NIM_ADD, byref(nid))

    def set_tooltip(self, text):
        self.tooltip = text
        self._nid.szTip = text[:127]
        self._nid.uFlags = NIF_TIP
        Shell_NotifyIconW(NIM_MODIFY, byref(self._nid))

    def balloon(self, title, text):
        nid = self._nid
        nid.uFlags = NIF_INFO
        nid.szInfo = text[:255]
        nid.szInfoTitle = title[:63]
        nid.dwInfoFlags = 1
        Shell_NotifyIconW(NIM_MODIFY, byref(nid))

    def _show_menu(self, items):
        hmenu = CreatePopupMenu()
        self._fill(hmenu, items)
        pos = POINT()
        GetCursorPos(byref(pos))
        SetForegroundWindow(self.hwnd)
        cmd = TrackPopupMenu(hmenu, TPM_RETURNCMD | TPM_RIGHTBUTTON | TPM_LEFTALIGN,
                             pos.x, pos.y, 0, self.hwnd, None)
        PostMessageW(self.hwnd, WM_NULL, 0, 0)
        DestroyMenu(hmenu)
        if cmd:
            self.on_command(cmd)

    def _fill(self, hmenu, items):
        for it in items:
            kind = it[0]
            if kind == "sep":
                AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
            elif kind == "item":
                _, mid, label, checked = it
                flags = MF_STRING
                if checked is True:
                    flags |= MF_CHECKED
                elif checked is False:
                    flags |= MF_UNCHECKED
                AppendMenuW(hmenu, flags, mid, label)
            elif kind == "sub":
                _, label, sub = it
                hs = CreatePopupMenu()
                self._fill(hs, sub)
                AppendMenuW(hmenu, MF_POPUP, hs, label)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            ev = lparam & 0xFFFF
            if ev == WM_RBUTTONUP:
                items = self._menu_provider() if self._menu_provider else self._menu_items
                if items:
                    self._show_menu(items)
            elif ev == WM_LBUTTONUP and self.on_activate:
                self.on_activate()
            return 0
        if msg == WM_COMMAND:
            if self.on_command:
                self.on_command(wparam & 0xFFFF)
            return 0
        if msg == WM_DESTROY:
            PostQuitMessage(0)
            return 0
        return DefWindowProcW(hwnd, msg, wparam, lparam)

    _menu_items = None

    def set_menu(self, items):
        self._menu_items = items

    def set_menu_provider(self, fn):
        self._menu_provider = fn

    def destroy(self):
        if self.hwnd:
            Shell_NotifyIconW(NIM_DELETE, byref(self._nid))
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
