from __future__ import annotations
import json,time
from dataclasses import dataclass
from pathlib import Path
from typing import List
from .state import EngineState,RequestState
from .models import Request
from .algorithms.base import Strategy
from .distance import euclidean

TRACE_SPEED=1.0
TRACE_SERVICE_TIME=1.0
@dataclass
class Event: time:float; request_id:int

class Simulator:
    """Runs unchanged route decisions and emits a separate, visual-only timeline."""
    def __init__(self,state:EngineState,strategy:Strategy,trace_enabled:bool=True):
        self.state=state; self.strategy=strategy; self.trace:List[dict]=[]; self.trace_enabled=trace_enabled
        self.response_times=[]; self.total_evaluations=0; self.route_disruption=0; self.phase_timings_ms={'insertion':0.0,'two_opt_star':0.0,'tabu':0.0}
    def _route_distance(self,routes:dict[int,tuple[int,...]])->float:
        total=0.
        for route in routes.values():
            point=(0.,0.)
            for rid in route: total+=euclidean(point,self.state.requests[rid].location); point=self.state.requests[rid].location
            total+=euclidean(point,(0.,0.))
        return total
    def _emit(self,event:dict)->None:
        if self.trace_enabled:self.trace.append(event)
    def _emit_motion_timeline(self,start_time:float)->None:
        """Visual movement events are derived from final routes; they never alter state."""
        for vehicle_id,vehicle in sorted(self.state.vehicles.items()):
            now=start_time; position=(0.,0.)
            for request_id in vehicle.route:
                request=self.state.requests[request_id]; travel=euclidean(position,request.location)/TRACE_SPEED
                self._emit({'time':now,'event':'vehicle_departed','vehicle_id':vehicle_id,'from':position,'to':request.location,'customer':request_id,'travel_time':travel})
                now+=travel; self._emit({'time':now,'event':'vehicle_arrived','vehicle_id':vehicle_id,'customer':request_id,'t':now})
                now+=TRACE_SERVICE_TIME; self._emit({'time':now,'event':'service_completed','vehicle_id':vehicle_id,'customer':request_id,'t':now})
                position=request.location
            if vehicle.route:
                travel=euclidean(position,(0.,0.))/TRACE_SPEED; self._emit({'time':now,'event':'vehicle_departed','vehicle_id':vehicle_id,'from':position,'to':(0.,0.),'customer':None,'travel_time':travel})
                now+=travel; self._emit({'time':now,'event':'vehicle_returned','vehicle_id':vehicle_id,'t':now})
    def run(self)->EngineState:
        events=sorted((Event(request.release_time,rid) for rid,request in self.state.requests.items()),key=lambda event:(event.time,event.request_id))
        for event in events:
            self.state.advance_time(event.time); request=self.state.requests[event.request_id]
            self._emit({'time':event.time,'event':'request_released','request_id':event.request_id,'release_time':request.release_time})
            if self.state.request_states[event.request_id]!=RequestState.AVAILABLE: continue
            before={vehicle_id:tuple(vehicle.route) for vehicle_id,vehicle in self.state.vehicles.items()}; before_distance=self._route_distance(before)
            started=time.perf_counter(); evaluations,new_state=self.strategy.update(self.state,request); elapsed_ms=(time.perf_counter()-started)*1000
            self.total_evaluations+=evaluations; self.response_times.append(elapsed_ms); self.state=new_state
            after={vehicle_id:tuple(vehicle.route) for vehicle_id,vehicle in self.state.vehicles.items()}; after_distance=self._route_distance(after)
            old_edges={(vehicle_id,left,right) for vehicle_id,route in before.items() for left,right in zip((-1,)+route,route+(-1,))}; new_edges={(vehicle_id,left,right) for vehicle_id,route in after.items() for left,right in zip((-1,)+route,route+(-1,))}
            moved=sum(1 for rid in self.state.requests if next((vehicle_id for vehicle_id,route in before.items() if rid in route),None)!=next((vehicle_id for vehicle_id,route in after.items() if rid in route),None)); self.route_disruption+=len(old_edges-new_edges)+moved
            phase='tabu' if self.strategy.__class__.__name__=='TabuSearch' else ('two_opt_star' if self.strategy.__class__.__name__=='GreedyThenTwoOptStar' else 'insertion'); self.phase_timings_ms[phase]+=elapsed_ms
            self._emit({'time':event.time,'event':'request_assigned','request_id':event.request_id,'evaluations':evaluations,'response_time_ms':elapsed_ms})
            self._emit({'time':event.time,'event':'route_updated','strategy':self.strategy.__class__.__name__,'routes':{str(vehicle_id):list(route) for vehicle_id,route in after.items()},'distance_delta':after_distance-before_distance,'evaluations':evaluations,'response_time_ms':elapsed_ms})
        self._emit_motion_timeline(max((event.time for event in events),default=0.0)+TRACE_SERVICE_TIME)
        self.trace.sort(key=lambda item:(item['time'],item['event']))
        return self.state
    def dump_trace(self,path:str|Path)->None:
        with open(path,'w',encoding='utf8') as handle:
            for entry in self.trace: handle.write(json.dumps(entry)+'\n')
