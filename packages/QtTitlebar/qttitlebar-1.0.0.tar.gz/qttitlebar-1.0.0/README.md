# Example

```python
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys

from QtTitlebar import QtTitlebar

application: QApplication = QApplication(sys.argv)
main: QMainWindow = QMainWindow()

titlebar: QtTitlebar = QtTitlebar(main)
titlebar.setTheme(QtTitlebar.ThemeType.Light)
# QtTitlebar.ThemeType.
# Supports Dark, Light, and System

main.show()
sys.exit(application.exec())
```