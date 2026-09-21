from engine.experiment_runner import strategy_factory
from engine.models import Scenario
from engine.scenarios import generate_scenario
from engine.simulator import Simulator
from engine.state import EngineState,RequestState
from engine.distance import build_matrix

def distance(state):
    matrix=build_matrix([(0.,0.)]+state.scenario.customer_locations); total=0.
    for vehicle in state.vehicles.values():
        nodes=[0]+[rid+1 for rid in vehicle.route]+[0]; total+=sum(matrix[a][b] for a,b in zip(nodes,nodes[1:]))
    return total

def test_rich_trace_does_not_change_seeded_metrics():
    config={'scenario':{'customers':8,'vehicles':2,'capacity':100,'dynamism':.4,'map_size':10.,'horizon':20.}}
    scenario=generate_scenario(config,31)
    plain=Simulator(EngineState(scenario),strategy_factory('greedy_insertion'),trace_enabled=False); rich=Simulator(EngineState(scenario),strategy_factory('greedy_insertion'),trace_enabled=True)
    plain_state=plain.run(); rich_state=rich.run()
    assert distance(plain_state)==distance(rich_state)
    assert plain.total_evaluations==rich.total_evaluations
    assert sum(s==RequestState.ASSIGNED for s in plain_state.request_states.values())==sum(s==RequestState.ASSIGNED for s in rich_state.request_states.values())
    assert {'request_released','route_updated','vehicle_departed','vehicle_arrived','service_completed','vehicle_returned'} <= {event['event'] for event in rich.trace}
