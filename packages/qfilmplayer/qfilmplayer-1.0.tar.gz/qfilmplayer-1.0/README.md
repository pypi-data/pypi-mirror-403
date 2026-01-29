# QFilmPlayer
## Видео плеер для Qt 6
## Версия 1.0

![](docs/screenshot.png)

### Установка

```shell
pip install git+https://gitflic.ru/project/nchistov/qfilmplayer.git
```

### Использование

QFilmPlayer можно использовать как отдельное окно, так и как виджет.

**examples/window_example.py**

```python
import sys

from PyQt6 import QtWidgets

import qfilmplayer

app = QtWidgets.QApplication(sys.argv)
fp = qfilmplayer.QFilmPlayer(["example_video.mp4"], title="QFilmPlayer")
fp.show()
sys.exit(app.exec())
```

**examples/widget_example.py**

```python
import sys

from PyQt6 import QtWidgets

from qfilmplayer import QFilmPlayer


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.grid = QtWidgets.QGridLayout()

        self.fp = QFilmPlayer(["example_video.mp4"])

        self.grid.addWidget(QtWidgets.QPushButton("Some button"), 1, 1)
        self.grid.addWidget(QtWidgets.QPushButton("Some another button"), 2, 1)
        self.grid.addWidget(QtWidgets.QPushButton("And another one"), 2, 2)
        self.grid.addWidget(self.fp, 1, 2)

        self.setLayout(self.grid)


app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
```

### Известные ошибки

 + Полноэкранный режим не работает, если QFilmPlayer встраивать как виджет
 + Если вы заметите какие-либо ошибки, [пишите](https://gitflic.ru/project/nchistov/qfilmplayer/issue)!

### Copyright

 + Код - © Николай Чистов, [Лицензия MIT](LICENSE)
 + `examples/example_video.mp4` - © Vincenzo Malagoli (https://www.pexels.com/@zenzazione/)
