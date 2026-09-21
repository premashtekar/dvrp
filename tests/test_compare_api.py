from fastapi.testclient import TestClient
from api import app

def test_compare_returns_three_runs_for_same_scenario():
    client=TestClient(app)
    scenario=client.post('/api/v1/scenarios',json={'customers':10,'vehicles':2,'capacity':100,'dynamism':.2,'seed':91,'map_size':100.,'horizon':480.}).json()
    response=client.post('/api/v1/compare',json={'scenario_id':scenario['id'],'strategies':['greedy_insertion','insertion_2opt_star','tabu_search'],'budget':{'max_evaluations':500}})
    assert response.status_code==200
    payload=response.json()
    assert payload['scenario_id']==scenario['id']
    assert len(payload['runs'])==3
    assert {run['scenario_id'] for run in payload['runs']}=={scenario['id']}
    assert {run['status'] for run in payload['runs']}=={'finished'}
