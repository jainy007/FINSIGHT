import subprocess
import time
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import threading
from webdriver_manager.chrome import ChromeDriverManager

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
    print(f"Starting {name} service...")

    # Log stdout and stderr in real-time
    def log_output():
        while process.poll() is None:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            if stdout_line:
                print(f"{name} stdout: {stdout_line.strip()}")
            if stderr_line:
                print(f"{name} stderr: {stderr_line.strip()}")

    log_thread = threading.Thread(target=log_output)
    log_thread.start()

    # Wait for the service to be ready
    if not wait_for_service(health_url):
        raise RuntimeError(f"{name} service failed to start")
    
    return process

def wait_for_service(url, retries=10, delay=5):
    """Wait for a service to be available by checking its health endpoint."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Service at {url} is ready!")
                return True
            else:
                print(f"Attempt {attempt+1}/{retries}: {url} returned status {response.status_code}")
        except requests.RequestException as e:
            print(f"Attempt {attempt+1}/{retries}: Failed to reach {url} - {e}")
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
                print(f"Attempt {attempt+1}/{retries}: {url} returned status {response.status_code}")
        except requests.RequestException as e:
            print(f"Attempt {attempt+1}/{retries}: Failed to reach {url} - {e}")
        time.sleep(delay)
    return False

def test_dashboard_service(headless=True):
    driver = None
    try:
        # Start all services
        market_process = start_service(MARKET_SERVICE_CMD, MARKET_PATH, "Market Data", SERVICE_HEALTH_URLS["Market Data"])
        sentiment_process = start_service(SENTIMENT_SERVICE_CMD, SENTIMENT_PATH, "Sentiment", SERVICE_HEALTH_URLS["Sentiment"])
        predictive_process = start_service(PREDICTIVE_SERVICE_CMD, PREDICTIVE_PATH, "Predictive", SERVICE_HEALTH_URLS["Predictive"])
        dashboard_process = start_service(DASHBOARD_SERVICE_CMD, DASHBOARD_PATH, "Dashboard", SERVICE_HEALTH_URLS["Dashboard"])

        print("Checking API health...")
        assert check_api_health("http://127.0.0.1:8000/ingest/AAPL"), "Market Data API unavailable"
        assert check_api_health("http://127.0.0.1:8001/analyze/AAPL"), "Sentiment API unavailable"
        assert check_api_health("http://127.0.0.1:5000/predict/AAPL"), "Predictive API unavailable"

        print("Setting up WebDriver...")
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        print("Opening dashboard...")
        try:
            driver.get(DASHBOARD_URL)
        except Exception as e:
            print(f"Error: {e}")
        try:
            WebDriverWait(driver, 30).until(EC.title_contains("Financial Insights"))
        except Exception as e:
            print(f"Error: {e}")

        print("Entering ticker AAPL...")
        ticker_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "input"))
        )
        ticker_input.clear()
        ticker_input.send_keys("AAPL")

        print("Clicking Fetch Data button...")
        fetch_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.TAG_NAME, "button"))
        )
        fetch_button.click()

        print("Waiting for charts to load...")
        time.sleep(30)

        print("Verifying chart elements...")
        stock_chart = driver.find_elements(By.TAG_NAME, "canvas")
        assert len(stock_chart) >= 2, f"Expected at least two chart canvases (stock and sentiment), found {len(stock_chart)} -> {stock_chart}"

        print("Verifying data presence...")
        stock_data_text = driver.find_elements(By.XPATH, "//p[contains(text(), 'Stock Data')]")
        print("STOCK_DATA_TEXT -> ", stock_data_text)
        sentiment_data_text = driver.find_elements(By.XPATH, "//p[contains(text(), 'Sentiment Data')]")
        print("SENTIMENT_DATA_TEXT -> ", sentiment_data_text)
        assert len(stock_data_text) > 0 and len(sentiment_data_text) > 0, "Data not displayed"

        print("Dashboard test passed!")

        if not headless:
            print("Test complete. Chrome window is open. Close the browser window to continue.")
            try:
                while True:
                    driver.title
                    time.sleep(1)
            except:
                print("Browser closed by user.")

    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        print("Cleaning up...")
        if driver:
            driver.quit()
        for process in [market_process, sentiment_process, predictive_process, dashboard_process]:
            process.terminate()
            process.wait()
        print("All services stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Financial Insights Dashboard service.")
    parser.add_argument('--headless', action='store_true', help="Run the test in headless mode")
    args = parser.parse_args()
    test_dashboard_service(headless=args.headless)