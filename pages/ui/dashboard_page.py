from pages.base_page import BaseWebPage

class DashboardPage():
    def __init__
        self.SEARCH_LOCATION = "[aria-label='Where are you going?']"

    def is_search_visible
        return self.actions.is_visible(self.SEARCH_LOCATION, timeout=5)