import sys
from PySide6 import QtWidgets, QtCore
from rbeesoft.app.ui.rbeesoftmainwindow import RbeesoftMainWindow
from rbeesoft.app.ui.widgets.pages.page import Page


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
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QtWidgets.QLabel(self.title()))
        layout.addWidget(button)
        self.setLayout(layout)

    def handle_button(self):
        self.switch_to_page('next')


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


def main():
    QtWidgets.QApplication.setApplicationName('example')
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowForward))
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()