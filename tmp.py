
from PyQt5.QtWidgets import (QMainWindow, QTextEdit,
                             QAction, QFileDialog, QApplication)
from PyQt5.QtGui import QIcon
import sys
from pathlib import Path


class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        openFile = QAction(QIcon('open.png'), 'Select Visualization File', self)
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        #menubar.addAction(openFile)
        fileMenu = menubar.addMenu('&Select File')
        fileMenu.addAction(openFile)

        self.show()

    def showDialog(self):

        home_dir = str(Path.home())
        fname = QFileDialog.getOpenFileName(self, 'Open file', home_dir)
        print(fname[0])


def main():
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()