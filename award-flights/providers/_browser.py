"""Shared headless-Chrome session for award providers (installed Chrome, temporary profile, no window)."""
import re, subprocess
from playwright.sync_api import TimeoutError as PwTimeout, sync_playwright

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class ProviderError(Exception):
    """A provider could not answer: blocked, rate-limited, logged out, or the site changed."""


def user_agent():
    # Headless Chrome announces "HeadlessChrome", which airline bot protection tarpits or blocks outright
    major = re.search(r"(\d+)\.", subprocess.run([CHROME_BIN, "--version"], capture_output=True, text=True).stdout).group(1)
    return (f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{major}.0.0.0 Safari/537.36")


class Browser:
    def __init__(self, locale="en-US", timeout=60000):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(channel="chrome", headless=True, args=[
            "--disable-blink-features=AutomationControlled", "--user-agent=" + user_agent()])
        self.context = self._browser.new_context(locale=locale, viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page.set_default_timeout(timeout)

    def close(self):
        self._browser.close()
        self._pw.stop()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def json_after(self, action, match, timeout=60000):
        """Run `action` (a navigation or click) and return the parsed JSON body of the first response
        whose URL satisfies `match` and whose status is 2xx."""
        try:
            with self.page.expect_response(lambda r: match(r.url) and 200 <= r.status < 300, timeout=timeout) as info:
                action()
            return info.value.json()
        except PwTimeout:
            raise ProviderError(f"no matching API response within {timeout // 1000}s (blocked, rate-limited, or the site changed)")
