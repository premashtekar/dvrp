// src/pages/SimulationReplay.tsx
import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';

interface TraceEvent {
  time: number;
  event: string;
  request_id?: number;
  evaluations?: number;
  delta?: number;
}

interface Scenario {
  customer_locations: [number, number][];
}

const SimulationReplay: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const [trace, setTrace] = useState<TraceEvent[]>([]);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      // try live API first
      let traceResp: string;
      try {
        const r = await axios.get<string>(`/api/v1/simulations/${runId}/trace`);
        traceResp = r.data;
      } catch {
        // fallback to static demo data
        const r = await axios.get<string>(`/demo/${runId}.jsonl`);
        traceResp = r.data;
      }
      const events = traceResp
        .trim()
        .split('\n')
        .map((line) => JSON.parse(line) as TraceEvent);
      setTrace(events);
      // also fetch scenario if possible
      try {
        const sc = await axios.get<Scenario>(`/api/v1/scenarios/${events[0]?.scenario_id || ''}`);
        setScenario(sc.data);
      } catch {
        // ignore
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  // Simple routes reconstruction (final state) for display
  const routes = useRef<Map<number, number[]>>(new Map());
  useEffect(() => {
    const map = new Map<number, number[]>();
    trace.forEach((ev) => {
      if (ev.event === 'request_assigned' && ev.request_id !== undefined) {
        // naive: assign to first vehicle (demo)
        const vid = 0;
        const arr = map.get(vid) || [];
        arr.push(ev.request_id);
        map.set(vid, arr);
      }
    });
    routes.current = map;
  }, [trace]);

  if (loading) return <div className="p-4">Loading replay…</div>;

  return (
    <div className="h-screen w-full">
      <Canvas camera={{ position: [0, 100, 200], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <directionalLight intensity={0.8} />
        <OrbitControls />
        {/* render depot */}
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[2, 16, 16]} />
          <meshStandardMaterial color="yellow" />
        </mesh>
        {/* render customers */}
        {scenario?.customer_locations.map((pt, idx) => (
          <mesh key={idx} position={[pt[0], 0, pt[1]]}>
            <sphereGeometry args={[1, 12, 12]} />
            <meshStandardMaterial color="gray" />
          </mesh>
        ))}
        {/* render routes (simplified) */}
        {Array.from(routes.current.entries()).map(([vid, route]) => {
          const points: [number, number, number][] = [];
          // start at depot
          points.push([0, 0, 0]);
          route.forEach((reqId) => {
            const loc = scenario?.customer_locations[reqId];
            if (loc) points.push([loc[0], 0, loc[1]]);
          });
          // back to depot
          points.push([0, 0, 0]);
          return (
            <Line
              key={vid}
              points={points as any}
              color={vid % 2 === 0 ? 'lime' : 'mint'}
              lineWidth={2}
            />
          );
        })}
      </Canvas>
    </div>
  );
};

export default SimulationReplay;
