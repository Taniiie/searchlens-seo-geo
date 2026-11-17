"""
Script to capture high-resolution screenshots of SearchLens dashboard using headless Chrome/Edge.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "screenshots")
os.makedirs(output_dir, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1600,1050")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

print("Initializing Chrome headless...")
driver = webdriver.Chrome(options=chrome_options)

try:
    print("Navigating to SearchLens on http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(6)  # Allow Streamlit and Plotly to fully render

    # 1. Capture Overview Dashboard
    overview_path = os.path.join(output_dir, "01_overview_dashboard.png")
    driver.save_screenshot(overview_path)
    print(f"Captured: {overview_path}")

    # Helper function to click sidebar radio options
    def click_nav_item(label_substr):
        labels = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="stRadio"] label')
        for l in labels:
            if label_substr.lower() in l.text.lower():
                l.click()
                time.sleep(4)
                return True
        return False

    # 2. Capture Website SEO Audit
    if click_nav_item("Website SEO Audit"):
        # Click Run Comprehensive SEO Audit
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(., 'Run Comprehensive SEO Audit')]")
            btn.click()
            time.sleep(5)
        except Exception as e:
            print("Run button note:", e)
        audit_path = os.path.join(output_dir, "02_website_audit.png")
        driver.save_screenshot(audit_path)
        print(f"Captured: {audit_path}")

    # 3. Capture E-Commerce SEO Suite
    if click_nav_item("E-Commerce SEO"):
        ecom_path = os.path.join(output_dir, "03_ecommerce_suite.png")
        driver.save_screenshot(ecom_path)
        print(f"Captured: {ecom_path}")

    # 4. Capture Keyword Intelligence
    if click_nav_item("Keyword Intelligence"):
        kw_path = os.path.join(output_dir, "04_keyword_intelligence.png")
        driver.save_screenshot(kw_path)
        print(f"Captured: {kw_path}")

    # 5. Capture GEO Research
    if click_nav_item("GEO Research"):
        geo_path = os.path.join(output_dir, "05_geo_research.png")
        driver.save_screenshot(geo_path)
        print(f"Captured: {geo_path}")

    print("All screenshots successfully captured!")

finally:
    driver.quit()
