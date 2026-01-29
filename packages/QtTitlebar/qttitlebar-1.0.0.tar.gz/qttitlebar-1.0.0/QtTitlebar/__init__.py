import ctypes
import ctypes.wintypes
import pathlib
import enum

module: ctypes.CDLL = ctypes.CDLL(pathlib.Path(__file__).parent.resolve() / "QtTitlebar.dll")

module.setTheme.argtypes = [ctypes.wintypes.HWND, ctypes.c_char_p]
module.setTheme.restype = None

module.setThemes.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
module.setThemes.restype = None

class QtTitlebar:
    class ThemeType(enum.Enum):
        Dark: str = "dark"
        Light: str = "light"
        System: str = "system"

        @property
        def bytes(self):
            return self.value.encode("UTF-8")

    def __init__(self, qtWindow) -> None:
        self.hwnd = qtWindow.winId()

    def setTheme(self, theme: ThemeType) -> None:
        module.setTheme(self.hwnd, theme.bytes)

    def setThemes(self, color, border) -> None:
        module.setThemes(self.hwnd, self._toHex(color), self._toHex(border))

    def _toHex(self, color) -> int:
        return (color.red() << 16) | (color.green() << 8) | color.blue()