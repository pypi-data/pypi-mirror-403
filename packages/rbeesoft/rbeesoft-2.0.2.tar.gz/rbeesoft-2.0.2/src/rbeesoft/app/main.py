import sys
from PySide6 import QtWidgets, QtCore
from rbeesoft.app.ui.rbeesoftmainwindow import RbeesoftMainWindow
from rbeesoft.app.ui.widgets.pages.page import Page
from rbeesoft.app.ui.processes.process import Process
from rbeesoft.app.ui.processes.processrunner import ProcessRunner


class MainWindow(RbeesoftMainWindow):
    def __init__(self, app_icon):
        super(MainWindow, self).__init__(
            bundle_identifier='rbeesoft.nl',
            app_name='example',
            app_title='Rbeesoft App Example',
            width=800,
            height=600,
            app_icon=app_icon,
        )
        self.add_page(HomePage(self.settings()), home_page=True)
        self.add_page(NextPage(self.settings()))


class HomePage(Page):
    def __init__(self, settings):
        super(HomePage, self).__init__('home', 'HomePage', settings)
        button = QtWidgets.QPushButton('Go to next page')
        button.clicked.connect(self.handle_button)
        process_button = QtWidgets.QPushButton('Run process')
        process_button.clicked.connect(self.handle_process_button)
        self._process_runner = ProcessRunner()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QtWidgets.QLabel(self.title()))
        layout.addWidget(button)
        layout.addWidget(process_button)
        self.setLayout(layout)

    def handle_button(self):
        self.switch_to_page('next')

    def handle_process_button(self):
        self._process_runner.start(ExampleProcess())


class NextPage(Page):
    def __init__(self, settings):
        super(NextPage, self).__init__('next', 'NextPage', settings)
        button = QtWidgets.QPushButton('Go to home page')
        button.clicked.connect(self.handle_button)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QtWidgets.QLabel(self.title()))
        layout.addWidget(button)
        self.setLayout(layout)

    def handle_button(self):
        self.switch_to_page('home')


class ExampleProcess(Process):
    def __init__(self):
        super(ExampleProcess, self).__init__()
        self._n = 10

    def execute(self):
        import time
        out = []
        for i in range(self._n):
            if self.is_canceled():
                return out
            time.sleep(0.25)
            out.append(i)
            self.progress.emit(int((i+1)/self._n*100))
        return out


def main():
    QtWidgets.QApplication.setApplicationName('example')
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowForward))
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()