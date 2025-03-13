### Python Automation Script: `validate_service.py`

#This script automates starting the service, testing the endpoint, 
#querying the database, and displaying results—all with one click. 
# It assumes your current setup (PostgreSQL running, virtual env active, etc.).


import subprocess
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
SERVICE_DIR = "market_data_service"
API_URL = "http://127.0.0.1:8000/ingest/AAPL"
DB_CONFIG = {
    "dbname": "market_data",
    "user": "postgres",
    "password": "password",  # Replace with your PostgreSQL password
    "host": "localhost",
    "port": "5432"
}

def start_service():
    """Start the Uvicorn server in a subprocess."""
    print("Starting the Market Data Ingestion Service...")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--reload"],
        cwd=SERVICE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait for the server to start
    time.sleep(3)  # Adjust if needed
    return process

def test_endpoint():
    """Test the /ingest/AAPL endpoint."""
    print("\nTesting the API endpoint...")
    try:
        response = requests.get(API_URL)
        print(f"API Response: {response.json()}")
    except requests.RequestException as e:
        print(f"Error testing endpoint: {e}")

def query_database():
    """Query the stock_data table and display results."""
    print("\nQuerying the database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM stock_data WHERE symbol = 'AAPL' LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            print("Database Results:")
            for row in rows:
                print(row)
        else:
            print("No data found in the database.")
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")

def main():
    """Run the full validation process."""
    # Start the service
    process = start_service()

    # Test the endpoint
    test_endpoint()

    # Query the database
    query_database()

    # Keep the service running until user stops it
    print("\nService is running. Press Ctrl+C to stop.")
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("Service stopped.")

if __name__ == "__main__":
    main()