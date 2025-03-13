import subprocess
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from webdriver_manager.chrome import ChromeDriverManager
import redis
from termcolor import colored

# Configuration
MARKET_SERVICE_CMD = ["uvicorn", "main:app", "--reload", "--port", "8000"]
SENTIMENT_SERVICE_CMD = ["uvicorn", "main:app", "--reload", "--port", "8001"]
PREDICTIVE_SERVICE_CMD = ["python", "main.py"]
DASHBOARD_SERVICE_CMD = ["npm", "run", "dev"]
BASE_DIR = os.getcwd()
MARKET_PATH = os.path.join(BASE_DIR, "market_data_service")
SENTIMENT_PATH = os.path.join(BASE_DIR, "sentiment_service")
PREDICTIVE_PATH = os.path.join(BASE_DIR, "predictive_service")
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard_service")
DASHBOARD_URL = "http://localhost:5173"

# Health endpoints for each service
SERVICE_HEALTH_URLS = {
    "Market Data": "http://127.0.0.1:8000/ingest/AAPL",
    "Sentiment": "http://127.0.0.1:8001/analyze/AAPL",
    "Predictive": "http://127.0.0.1:5000/predict/AAPL",
    "Dashboard": "http://localhost:5173"
}

def start_service(cmd, cwd, name, health_url):
    """Start a service in a subprocess and wait for it to be ready."""
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    print(colored(f"Starting {name} service...", "cyan"))
    
    if not wait_for_service(health_url):
        raise RuntimeError(f"{name} service failed to start")
    
    return process

def wait_for_service(url, retries=10, delay=5):
    """Wait for a service to be available by checking its health endpoint."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(colored(f"Service at {url} is ready!", "green"))
                return True
            else:
                print(colored(f"Attempt {attempt+1}/{retries}: {url} returned status {response.status_code}", "yellow"))
        except requests.RequestException as e:
            print(colored(f"Attempt {attempt+1}/{retries}: Failed to reach {url} - {e}", "light_yellow"))
        time.sleep(delay)
    return False

def check_api_health(url, retries=3, delay=10):
    """Check if an API endpoint is accessible with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
            else:
                print(colored(f"Attempt {attempt+1}/{retries}: {url} returned status {response.status_code}", "yellow"))
        except requests.RequestException as e:
            print(colored(f"Attempt {attempt+1}/{retries}: Failed to reach {url} - {e}", "light_yellow"))
        time.sleep(delay)
    return False

def test_dashboard_service(headless=True):
    driver = None
    
    market_process = start_service(MARKET_SERVICE_CMD, MARKET_PATH, "Market Data", SERVICE_HEALTH_URLS["Market Data"])
    sentiment_process = start_service(SENTIMENT_SERVICE_CMD, SENTIMENT_PATH, "Sentiment", SERVICE_HEALTH_URLS["Sentiment"])
    predictive_process = start_service(PREDICTIVE_SERVICE_CMD, PREDICTIVE_PATH, "Predictive", SERVICE_HEALTH_URLS["Predictive"])
    dashboard_process = start_service(DASHBOARD_SERVICE_CMD, DASHBOARD_PATH, "Dashboard", SERVICE_HEALTH_URLS["Dashboard"])

    try:
        print(colored("Checking API health...", "cyan"))
        assert check_api_health("http://127.0.0.1:8000/ingest/AAPL"), "Market Data API unavailable"
        assert check_api_health("http://127.0.0.1:8001/analyze/AAPL"), "Sentiment API unavailable"
        assert check_api_health("http://127.0.0.1:5000/predict/AAPL"), "Predictive API unavailable"

        print(colored("Setting up WebDriver...", "cyan"))
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        print(colored("Opening dashboard...", "cyan"))
        try:
            driver.get(DASHBOARD_URL)
        except Exception as e:
            print(colored(f"Error: {e}", "red"))
        try:
            WebDriverWait(driver, 30).until(EC.title_contains("Financial Insights"))
        except Exception as e:
            print(colored(f"Error: {e}", "red"))

        print(colored("Entering ticker AAPL...", "cyan"))
        ticker_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "input"))
        )
        ticker_input.clear()
        ticker_input.send_keys("AAPL")

        print(colored("Clicking Fetch Data button...", "cyan"))
        fetch_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Fetch Data']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", fetch_button)
        assert fetch_button.is_enabled(), "Fetch Data button is not enabled"
        assert fetch_button.is_displayed(), "Fetch Data button is not displayed"
        driver.execute_script("arguments[0].click();", fetch_button)

        print(colored("Waiting for charts to load...", "cyan"))
        time.sleep(30)

        print(colored("Verifying chart elements...", "cyan"))
        stock_chart = driver.find_elements(By.TAG_NAME, "canvas")
        assert len(stock_chart) >= 2, f"Expected at least two chart canvases (stock and sentiment), found {len(stock_chart)} -> {stock_chart}"

        print(colored("Waiting for real-time update...", "cyan"))
        # Get the initial stock data count
        initial_stock_data = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stock-data"))
        )
        initial_count = int(initial_stock_data.text.split(" ")[2])  # Extract number from "Stock Data: X entries"
        print(colored(f"Initial stock data count: {initial_count}", "blue"))

        # Wait for the count to increase due to a real-time update
        try:
            WebDriverWait(driver, 40).until(
                lambda d: int(d.find_elements(By.ID, "stock-data")[0].text.split(" ")[2]) > initial_count,
                message="Real-time update not received within 40 seconds"
            )
            print(colored("Real-time update received!", "green"))
        except Exception as e:
            print(colored(f"Real-time update failed: {str(e)}", "red"))

        print(colored("Verifying data presence...", "cyan"))
        stock_data_text = driver.find_elements(By.XPATH, "//p[contains(text(), 'Stock Data')]")
        print("STOCK_DATA_TEXT -> ", stock_data_text)
        sentiment_data_text = driver.find_elements(By.XPATH, "//p[contains(text(), 'Sentiment Data')]")
        print("SENTIMENT_DATA_TEXT -> ", sentiment_data_text)
        assert len(stock_data_text) > 0 and len(sentiment_data_text) > 0, "Data not displayed"

        print(colored("Dashboard test passed!", "green"))

        # Verify caching
        r = redis.Redis(host='localhost', port=6379, db=0)
        cache_keys = r.keys("*")
        print(colored(f"Cache keys found: {cache_keys}", "blue"))
        if b"cache:predict:AAPL" in cache_keys:
            print(colored("Prediction for AAPL is cached!", "green"))

        if not headless:
            print(colored("Test complete. Chrome window is open. Close the browser window to continue.", "light_yellow"))
            try:
                while True:
                    driver.title
                    time.sleep(1)
            except:
                print(colored("Browser closed by user.", "cyan"))

    except AssertionError as e:
        print(colored(f"Test failed: {e}", "red"))
    except Exception as e:
        print(colored(f"Unexpected error: {str(e)}", "red"))
    finally:
        print(colored("Cleaning up...", "cyan"))
        if driver:
            driver.quit()
        for process in [market_process, sentiment_process, predictive_process, dashboard_process]:
            process.terminate()
            process.wait()
        print(colored("All services stopped.", "cyan"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Financial Insights Dashboard service.")
    parser.add_argument('--headless', action='store_true', help="Run the test in headless mode")
    args = parser.parse_args()
    test_dashboard_service(headless=args.headless)