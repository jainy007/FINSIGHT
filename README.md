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
docker compose up --build
```

2. Run the test
```
python test_dashboard_dockerized.py
```