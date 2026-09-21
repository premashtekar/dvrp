import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, Navigate } from 'react-router-dom';

const Nav = () => (
  <nav className="flex gap-4 p-4 border-b border-[var(--accent-1)] mb-4">
    <Link to="/results">Results</Link>
    <Link to="/replay">Replay</Link>
    <Link to="/compare">Compare</Link>
    <Link to="/experiments">Experiments</Link>
    <Link to="/methodology">Methodology</Link>
  </nav>
);

const Banner = () => (
  <div className="bg-[var(--accent-2)] text-black p-2 text-center text-sm font-bold">
    Precomputed from real engine runs (3 seeds)
  </div>
);

const Results = () => {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    fetch('/demo/results.json').then(r => r.json()).then(setData).catch(console.error);
  }, []);
  
  if (!data) return <div className="p-4">Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl text-[var(--accent-1)] mb-4">Results</h1>
      <a href="/demo/results.json" download className="border p-1 text-sm inline-block mb-4">Download CSV (JSON)</a>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="border p-2 border-[var(--accent-2)]">
          <h2 className="text-xl">Aggregated Stats (n=3)</h2>
          <table className="w-full mt-2">
            <thead>
              <tr className="text-left text-[var(--accent-1)]">
                <th>Strategy</th><th>Mean Time (s)</th><th>Mean Evals</th><th>Mean Delta Dist</th>
              </tr>
            </thead>
            <tbody>
              {data.aggregated.map((a: any) => (
                <tr key={a.strategy}>
                  <td>{a.strategy}</td>
                  <td>{a.mean_time_s.toFixed(4)}</td>
                  <td>{a.mean_evaluations.toFixed(1)}</td>
                  <td>{a.mean_delta_distance?.toFixed(2) || '0.00'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border p-2 border-[var(--accent-2)]">
          <h2 className="text-xl">Paired Statistics</h2>
          <pre className="text-xs mt-2 overflow-auto">{JSON.stringify(data.paired_stats, null, 2)}</pre>
        </div>
      </div>
      
      <div className="mt-4 border p-2 border-[var(--accent-2)]">
        <h2 className="text-xl mb-2">Charts & Scatter (Placeholder)</h2>
        <div className="h-32 flex items-center justify-center border border-dashed">
           (Quality vs Compute scatter and Charts with error bars would render here based on data.per_run)
        </div>
      </div>
    </div>
  );
};

const Compare = () => {
  const [data, setData] = useState<any>(null);
  const [strategy, setStrategy] = useState('greedy_insertion');
  useEffect(() => { fetch('/demo/results.json').then(r => r.json()).then(setData); }, []);
  
  return (
    <div className="p-4">
      <h1 className="text-2xl text-[var(--accent-1)] mb-4">Compare</h1>
      <select className="bg-[var(--bg-color)] text-[var(--text-color)] border p-1 mb-4" value={strategy} onChange={e => setStrategy(e.target.value)}>
         <option value="greedy_insertion">Greedy</option>
         <option value="insertion_2opt_star">2-Opt*</option>
         <option value="tabu_search">Tabu Search</option>
      </select>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="border p-2">
           <h2 className="text-[var(--accent-2)] mb-2">Metrics for {strategy}</h2>
           {data ? (
             <pre className="text-xs">
               {JSON.stringify(data.aggregated.find((a:any)=>a.strategy===strategy), null, 2)}
             </pre>
           ) : 'Loading...'}
        </div>
        <div className="border p-2">
           <h2 className="text-[var(--accent-2)]">Side-by-side Viewport (Mock)</h2>
           <div className="mt-2 h-32 flex items-center justify-center border border-dashed">Viewport showing {strategy} route</div>
        </div>
      </div>
    </div>
  );
};

const Replay = () => (
  <div className="p-4">
    <h1 className="text-2xl text-[var(--accent-1)] mb-4">Replay</h1>
    <p>Select a run from results to replay here. Reads from /demo/traces (mocked).</p>
  </div>
);

const Experiments = () => (
  <div className="p-4">
    <h1 className="text-2xl text-[var(--accent-1)] mb-4">Experiments Configuration</h1>
    <div className="border p-4 inline-block">
       <p>Customers: 50</p>
       <p>Dynamism: 0.1, 0.4, 0.8</p>
       <p>Strategies: A, B, C</p>
       <p>Seeds: 3</p>
       <button disabled className="mt-4 p-2 border opacity-50 cursor-not-allowed">Run Batch</button>
       <p className="text-xs text-[var(--accent-2)] mt-1">Requires the backend</p>
    </div>
  </div>
);

const Methodology = () => (
  <div className="p-4 max-w-2xl">
    <h1 className="text-2xl text-[var(--accent-1)] mb-4">Methodology</h1>
    <p>This prototype compares Greedy Insertion, Greedy + 2-Opt* Repair, and Tabu Search on dynamic VRP instances.</p>
    <p className="mt-2">Configuration used:</p>
    <ul className="list-disc pl-5">
      <li>Customers: 50</li>
      <li>Vehicles: 5</li>
      <li>Dynamism: 0.1, 0.4, 0.8</li>
      <li>Tabu Budget: 200 evaluations (reduced for quick pilot)</li>
      <li>Adaptive selector: Skipped (future work)</li>
    </ul>
  </div>
);

const App = () => (
  <div className="min-h-screen">
    <Banner />
    <Nav />
    <Routes>
      <Route path="/" element={<Navigate to="/results" replace />} />
      <Route path="/results" element={<Results />} />
      <Route path="/compare" element={<Compare />} />
      <Route path="/replay" element={<Replay />} />
      <Route path="/experiments" element={<Experiments />} />
      <Route path="/methodology" element={<Methodology />} />
    </Routes>
  </div>
);

export default App;
