import json
from pathlib import Path
from fastapi.testclient import TestClient
from api import app

def test_results_matches_static_export_for_one_cell():
    response=TestClient(app).get('/api/v1/results')
    assert response.status_code == 200
    live=response.json()
    static=json.loads((Path(__file__).parents[1]/'web'/'public'/'demo'/'results.json').read_text(encoding='utf8'))
    live_cell=next(row for row in live['aggregated'] if row['customers']==50 and row['dynamism']==0.1 and row['strategy']=='greedy_insertion')
    static_cell=next(row for row in static['aggregated'] if row['customers']==50 and row['dynamism']==0.1 and row['strategy']=='greedy_insertion')
    assert live_cell['metrics']['total_distance']['mean'] == static_cell['metrics']['total_distance']['mean']
    assert live_cell['metrics']['total_distance']['n'] == static_cell['metrics']['total_distance']['n']
