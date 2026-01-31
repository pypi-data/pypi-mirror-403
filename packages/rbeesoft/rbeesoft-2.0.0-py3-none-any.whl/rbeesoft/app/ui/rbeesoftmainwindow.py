from PySide6.QtCore import Qt, QByteArray
from PySide6.QtWidgets import QMainWindow, QStyle
from PySide6.QtGui import QGuiApplication, QAction
from rbeesoft.app.ui.settings import Settings
from rbeesoft.app.ui.widgets.centraldockwidget import CentralDockWidget
from rbeesoft.app.ui.widgets.logdockwidget import LogDockWidget
from rbeesoft.common.logmanager import LogManager

LOG = LogManager()


class RbeesoftMainWindow(QMainWindow):
    def __init__(self, bundle_identifier, app_name, app_title, width=1024, height=1024, app_icon=None):
        super(RbeesoftMainWindow, self).__init__()
        self._settings = Settings(bundle_identifier, app_name)
        self._app_title = app_title
        self._width = width
        self._height = height
        self._app_icon = app_icon
        self._central_dockwidget = CentralDockWidget(self, self._settings)
        self._log_dockwidget = LogDockWidget(self)
        self.init()

    # INITIALIZATION

    def init(self):
        self.setWindowTitle(self._app_title)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self._central_dockwidget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._log_dockwidget)
        if self._app_icon:
            self.setWindowIcon(self._app_icon)
        self.load_geometry_and_state()
        self.init_default_menus()
        self.statusBar().showMessage('Ready')
        LOG.info(f'Settings path: {self.settings().fileName()}')

    def init_default_menus(self):
        exit_action_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        exit_action = QAction(exit_action_icon, 'E&xit', self)
        exit_action.triggered.connect(self.close)
        application_menu = self.menuBar().addMenu('Application')
        application_menu.addAction(exit_action)

    # GETTERS

    def settings(self):
        return self._settings
    
    # EVENT HANDLERS

    def closeEvent(self, _):
        self.save_geometry_and_state()

    # HELPERS

    def add_page(self, page, home_page=False):
        self._central_dockwidget.add_page(page, home_page)

    def load_geometry_and_state(self):
        geometry = self.settings().get('mainwindow/geometry')
        state = self.settings().get('mainwindow/state')
        if isinstance(geometry, QByteArray) and self.restoreGeometry(geometry):
            if isinstance(state, QByteArray):
                self.restoreState(state)
            return
        self.resize(self._width, self._height)
        self.center_window()        

    def save_geometry_and_state(self):
        self.settings().set('mainwindow/geometry', self.saveGeometry())
        self.settings().set('mainwindow/state', self.saveState())

    def center_window(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.geometry().width()) / 2
        y = (screen.height() - self.geometry().height()) / 2
        self.move(int(x), int(y))