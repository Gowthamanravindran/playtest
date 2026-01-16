# from pages.base_page import BaseWebPage
from adapters.ui.ui_actions_impl import PlaywrightUIActions

class DashboardPage():
    def __init__(self, page=None):
        self.SEARCH_LOCATION = "[aria-label='Where are you going?']"
        self.actions = PlaywrightUIActions(page) if page else None

    def is_search_visible(self):
        return self.actions.is_visible(self.SEARCH_LOCATION, timeout=5)