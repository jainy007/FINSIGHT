# System Setup:

### Prerequisites
```
sudo apt-get update
sudo apt-get install python3.10 python3.10-dev python3-pip
sudo apt-get install nodejs npm
----keep node version >=18
sudo apt-get install containerd docker.io
sudo apt-get install docker-compose-plugin
```

### Install and Start Redis:

```
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```


### Setup PostGreSQL

```
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```
---enter postgres#
```
sudo -u postgres psql
```

---create database and user
```
CREATE DATABASE market_data_db;
CREATE USER market_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE market_data_db TO market_user;
\q
```


### Setup VENV

```
python3 -m venv venv
source venv/bin/activate
```

--- from venv, run the following:

```
sudo apt-get install -y llvm
pip install -r market_data_service/requirements.txt
pip install -r sentiment_service/requirements.txt
pip install -r predictive_service/requirements.txt
pip install -r dashboard_service/requirements.txt
pip install requests selenium termcolor redis webdriver-manager
```
--- if you have GPU
```
pip install Xformers
```

--- from dashboard_service

```
npm install date-fns
npm run build
```

### Manually start microservices

1. **Redis Server**

```
redis-server --port 6379
```
```
---- Verify : 
        $ redis-cli ping
        PONG
```

2. **Market Data Service**
```
cd market_data_service
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Sentiment Service**
```
cd sentiment_service
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001
```

--- Verify
```
    curl http://localhost:8001/analyze/AAPL
```    
Expected: {"symbol":"AAPL","sentiment_score":0.5,...} (or similar)

4. **Predictive Service**

```
cd predictive_service
python main.py
```

--- Verify
```
    curl http://localhost:5000/predict/AAPL
```
Expected: {"symbol":"AAPL","predicted_close":220.92349243164062}

5. **Dashboard Service** BACKEND

```
cd dashboard_service
uvicorn main:app --host 0.0.0.0 --port 8002
```
--- Verify
```
    curl http://localhost:8002/health
```
Expected: {"status":"healthy"}

6. **Dashboard Service** FRONTEND

```
npm run dev
```

--- Verify

- Open `http://localhost:5173` in a browser
- Log in with testuser/testpassword (or sign up).
- After logging in, you should be redirected to the dashboard (/dashboard), where you can enter a ticker (e.g., AAPL) and fetch data

--- Automated Verify
```
python test_dashboard_service_cache_auth.py
```
- Automated microservices deploy
- Check microservice health
- Check overall performance, cacheing, auth etc.

### Setup Dockerization and run full deployment

1. From root, build and run all services
```
docker-compose up --build
```

2. Run the test
```
python test_dashboard_dockerized.py
```