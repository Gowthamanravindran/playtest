

@allure.epic("dashboard pages")
def test_dashboard
    dashboard_page = DashboardPage()
    expect(dashboard_page.is_search_visible).toBeTruthy();

    