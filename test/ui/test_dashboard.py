import allure
from pages.ui import DashboardPage
from playwright.sync_api import expect

@allure.suite("Dashboards")
class TestDashboard:
    @allure.story("Dashboard Load")
    @allure.title("Verify search element is visible")
    def test_dashboard(self, page, test_config):
        # Navigate to the base URL
        page.goto(test_config.data.ui.base_url)
        
        dashboard_page = DashboardPage(page)
        assert dashboard_page.is_search_visible() is True

    