"""Smoke tests for the TrackShift upgrade. Run: python test_trackshift_upgrade.py"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

stints = client.get('/tyre-intel/stints').json()
assert stints['stints'], 'No demo stints returned'
sid = stints['defaultStintId']

result = client.post('/tyre-intel/decision-value', json={'stintId': sid, 'budget': 100})
assert result.status_code == 200
body = result.json()
assert 'actions' in body and 'recommendation' in body
assert body['resourcePrinciple'].startswith('Resource Credits')

assumptions = client.get('/tyre-intel/model-assumptions')
assert assumptions.status_code == 200

with open('sample_telemetry.csv', 'rb') as f:
    upload = client.post('/tyre-intel/session/upload', files={'file': ('sample.csv', f, 'text/csv')})
assert upload.status_code == 200
assert upload.json()['lapCount'] == 8

client.post('/tyre-intel/session/use-demo')
print('TrackShift upgrade smoke tests: PASS')
