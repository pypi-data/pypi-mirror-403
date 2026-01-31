import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from robin_local_logger import init_robin_logger

def test_fastapi_integration(tmp_path):
    app = FastAPI()
    log_file = tmp_path / "fastapi_robin.log"
    API_KEY = "test-key"
    init_robin_logger(app, log_file=str(log_file), max_mb=1.0, api_key=API_KEY)
    
    client = TestClient(app)
    headers = {"X-API-Key": API_KEY}
    
    # POST
    payload = {"message": "Test FastAPI log", "level": "info"}
    response = client.post("/robin/logs", json=payload, headers=headers)
    assert response.status_code == 200
    
    # GET
    response = client.get("/robin/logs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert any(log.get("message") == "Test FastAPI log" for log in data["logs"])

def test_fastapi_trimming(tmp_path):
    app = FastAPI()
    log_file = tmp_path / "trim.log"
    # Small MB to trigger trimming
    init_robin_logger(app, log_file=str(log_file), max_mb=0.0001)
    client = TestClient(app)
    
    for i in range(50):
        client.post("/robin/logs", json={"message": f"line {i}"})
    
    assert os.path.exists(log_file)
    assert os.path.getsize(log_file) < 2000
    
    response = client.get("/robin/logs?lines=5")
    assert response.status_code == 200
    assert len(response.json()["logs"]) <= 5
