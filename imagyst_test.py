import pytest
from dpqa.zoetisqa.helpers.navigation import MenuHelper
from dpqa.zoetisqa.screens.settings import Settings
from dpqa.zoetisqa.helpers.settings import DevicesHelper
from zoetisqa.helpers import Logger, wait_for_element
from zoetisqa.helpers.settings import SettingsHelper
from zoetisqa.helpers import BrowserBase, Logger

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestImagyst:

    def test_imagyst_connection(self, hub_app):

        Logger.info("Starting Imagyst connection test...")

        menu = MenuHelper()
        menu.settings_tab()
        Logger.info("Opened Settings tab.")
        browser = BrowserBase.current_browser
        wait = WebDriverWait(browser, 15)

        settings_screen = Settings()
        settings_screen.devices().click()
        Logger.info("Opened Devices tab.")

        imagyst_tab_locators = [
            (By.ID, "hub.settings.devices.imagyst-tab"),
            (By.CSS_SELECTOR, '[id="hub.settings.devices.imagyst"]'),
            (By.XPATH, "//*[@role='tab' and (normalize-space()='Vetscan Imagyst' or contains(., 'Imagyst'))]"),
            (By.XPATH, "//button[normalize-space()='Vetscan Imagyst' or contains(., 'Imagyst')]"),
            (By.XPATH, "//a[contains(@href,'imagyst') or contains(@id,'imagyst')]"),
        ]

        opened_imagyst = False
        for by, sel in imagyst_tab_locators:
            try:
                el = wait.until(EC.element_to_be_clickable((by, sel)))
                browser.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.click()
                opened_imagyst = True
                break
            except Exception:
                continue

        assert opened_imagyst, "Could not find/click Vetscan Imagyst tab on Devices page."
        Logger.info("Opened Vetscan Imagyst tab.")

        # 4) Attempt to connect
        devices_helper = DevicesHelper()
        email = "muktar.hassen@zoetis.com"
        password = "DPQAAutomation#2025"

        Logger.info("Attempting to connect to Imagyst...")
        devices_helper.connect_to_imagys(email, password)
        Logger.info("Connected")
