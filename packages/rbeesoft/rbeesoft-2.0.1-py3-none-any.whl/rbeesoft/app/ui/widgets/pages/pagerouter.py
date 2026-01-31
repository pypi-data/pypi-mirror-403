from PySide6.QtWidgets import QStackedWidget


class PageRouter(QStackedWidget):
    def __init__(self):
        super(PageRouter, self).__init__()
        self._pages = {}
        self._home_page = None
        self._current_page = None
        self._previous_page = None

    def pages(self):
        return self._pages
    
    def page(self, name):
        if name in self.pages().keys():
            return self.pages()[name]
        return None
    
    def home_page(self):
        return self._home_page
    
    def current_page(self):
        return self._current_page
    
    def previous_page(self):
        return self._previous_page
    
    def add_page(self, page, home_page=False):
        if page.name() not in self.pages().keys():
            self.pages()[page.name()] = page
            if home_page:
                self._home_page = page
            self.addWidget(page)
    
    def switch_to_page(self, name):
        if self._current_page and name == self._current_page.name():
            return
        if self._current_page:
            self._previous_page = self._current_page
        self._current_page = self.page(name)
        self.setCurrentWidget(self._current_page)

    def switch_to_home(self):
        if self._current_page:
            self._previous_page = self._current_page
        self._current_page = self._home_page
        self.setCurrentWidget(self._current_page)
