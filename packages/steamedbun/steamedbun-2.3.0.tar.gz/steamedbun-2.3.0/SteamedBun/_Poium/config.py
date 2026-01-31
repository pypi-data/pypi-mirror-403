"""
@Author: 馒头 (chocolate)
@Email: neihanshenshou@163.com
@File: Config.py
@Time: 2023/12/9 18:00
"""
import threading


class BrowserObject:

    # Default playwright page driver
    page = None

    # Adds a border to the action element of the operation
    show = True

    # selenium screenshot path and If you want to use, you need to set your own
    selenium_screenshot_path = None

    # playwright screenshot path and If you want to use, you need to set your own
    playwright_screenshot_path = None

    _thread_local = threading.local()

    @property
    def driver(self):
        """
        Browser driver
        """
        return getattr(self._thread_local, 'driver', None)

    @driver.setter
    def driver(self, value):
        self._thread_local.driver = value

    @property
    def action(self):
        """
        Playwright locator action
        """
        return getattr(self._thread_local, 'action', None)

    @action.setter
    def action(self, value):
        self._thread_local.action = value
