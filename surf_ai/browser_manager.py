from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self, command_timeout: int):
        self.command_timeout = command_timeout
        self.playwright = sync_playwright().start()
        
    def create_browser(self):
        browser = self.playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        return browser

    def create_context(self, browser):
        context = browser.new_context(
            viewport={'width': 1280, 'height': 960},
            device_scale_factor=1,
            bypass_csp=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
        """)
        return context

    def create_page(self, context):
        page = context.new_page()
        page.set_default_timeout(self.command_timeout)
        return page