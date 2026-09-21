import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ScatterChart, Scatter, ResponsiveContainer, ErrorBar } from 'recharts';

const colors = {
  greedy_insertion: '#F2FFE9',
  insertion_2opt_star: '#39FF88',
  tabu_search: '#B4FF39'
};

const labels = {
  greedy_insertion: 'Greedy',
  insertion_2opt_star: '2-Opt*',
  tabu_search: 'Tabu Search'
};

const Nav = () => {
  const loc = useLocation();
  const cls = (path: string) => `px-3 py-2 rounded-md font-sans text-sm font-medium ${loc.pathname === path ? 'bg-[var(--accent-2)] text-black' : 'text-[var(--text-color)] hover:text-[var(--accent-1)]'}`;
  return (
    <nav className="flex gap-4 p-4 border-b border-[var(--accent-1)] bg-[#0B0F0A] sticky top-0 z-10 items-center">
      <span className="font-bold text-lg text-[var(--accent-1)] mr-4">DVRP Engine</span>
      <Link className={cls('/overview')} to="/overview">Overview</Link>
      <Link className={cls('/results')} to="/results">Results</Link>
      <Link className={cls('/compare')} to="/compare">Compare</Link>
      <Link className={cls('/lab')} to="/lab">Scenario Lab</Link>
      <Link className={cls('/replay')} to="/replay">Replay</Link>
      <Link className={cls('/experiments')} to="/experiments">Experiments</Link>
      <Link className={cls('/methodology')} to="/methodology">Methodology</Link>
    </nav>
  );
};

const Banner = () => (
  <div className="bg-[var(--accent-2)] text-black p-1 text-center text-xs font-bold uppercase tracking-wider">
    Precomputed from real engine runs (3 seeds)
  </div>
);

const Card = ({ children, title }: { children: React.ReactNode, title?: string }) => (
  <div className="bg-[#111] border border-[#333] rounded-lg p-6 shadow-lg mb-6">
    {title && <h2 className="text-xl font-sans font-semibold text-[var(--accent-1)] mb-4">{title}</h2>}
    {children}
  </div>
);

const RequiresBackend = () => (
  <Card title="Requires Backend">
    <p className="text-sm font-sans text-gray-400">This feature requires a live engine backend to generate new simulations dynamically.</p>
  </Card>
);

const Overview = () => (
  <div className="p-6 max-w-4xl mx-auto font-sans">
    <h1 className="text-3xl font-bold text-[var(--accent-1)] mb-4">DVRP Engine</h1>
    <p className="mb-4 text-gray-300">Welcome to the Dynamic Vehicle Routing Problem Engine prototype. Use the navigation bar to explore the precomputed experiment results.</p>
  </div>
);

const Results = () => {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    fetch('/demo/results.json').then(r => r.json()).then(setData).catch(console.error);
  }, []);
  
  if (!data) return <div className="p-6 font-sans text-gray-400">Loading metrics...</div>;

  // Prepare chart data
  const chartDataDyn = [0.1, 0.4, 0.8].map(dyn => {
    const pt: any = { dynamism: dyn };
    data.aggregated.filter((a: any) => a.dynamism === dyn).forEach((a: any) => {
      pt[`${a.strategy}_dist`] = a.mean_distance;
      pt[`${a.strategy}_dist_err`] = [a.mean_distance - a.se_distance, a.mean_distance + a.se_distance];
      const pr = data.per_run.filter((r:any) => r.dynamism === dyn && r.strategy === a.strategy);
      const times = pr.map((r:any) => r.metrics.total_time_s);
      const disr = pr.map((r:any) => r.metrics.route_disruption);
      pt[`${a.strategy}_time`] = times.reduce((s:number,v:number)=>s+v,0)/times.length;
      pt[`${a.strategy}_disr`] = disr.reduce((s:number,v:number)=>s+v,0)/disr.length;
    });
    return pt;
  });

  const scatterData = data.aggregated.map((a: any) => {
    const pr = data.per_run.filter((r:any) => r.dynamism === a.dynamism && r.strategy === a.strategy);
    const times = pr.map((r:any) => r.metrics.total_time_s);
    return {
      strategy: a.strategy,
      time: times.reduce((s:number,v:number)=>s+v,0)/times.length,
      dist: a.mean_distance
    };
  });

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6 font-sans">
        <h1 className="text-3xl font-bold text-[var(--accent-1)]">Experiment Results</h1>
        <a href="/demo/aggregated.csv" download className="bg-[var(--accent-1)] text-black px-4 py-2 rounded-md font-semibold hover:bg-[var(--accent-2)] transition-colors">Download CSV</a>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Total Distance vs Dynamism (n=3)">
          <div className="h-64 font-mono text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartDataDyn} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="dynamism" stroke="#888" label={{ value: 'Dynamism', position: 'insideBottomRight', offset: -10, fill: '#888' }} />
                <YAxis stroke="#888" label={{ value: 'Distance', angle: -90, position: 'insideLeft', fill: '#888' }} />
                <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                <Legend />
                {Object.keys(colors).map(strat => (
                  <Line key={strat} type="monotone" dataKey={`${strat}_dist`} name={labels[strat as keyof typeof labels]} stroke={colors[strat as keyof typeof colors]} strokeWidth={2}>
                     <ErrorBar dataKey={`${strat}_dist_err`} width={4} strokeWidth={2} stroke={colors[strat as keyof typeof colors]} />
                  </Line>
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Compute Time vs Dynamism">
          <div className="h-64 font-mono text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartDataDyn} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="dynamism" stroke="#888" label={{ value: 'Dynamism', position: 'insideBottomRight', offset: -10, fill: '#888' }} />
                <YAxis stroke="#888" label={{ value: 'Time (s)', angle: -90, position: 'insideLeft', fill: '#888' }} />
                <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                <Legend />
                {Object.keys(colors).map(strat => (
                  <Line key={strat} type="monotone" dataKey={`${strat}_time`} name={labels[strat as keyof typeof labels]} stroke={colors[strat as keyof typeof colors]} strokeWidth={2} strokeDasharray="5 5" />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Route Disruption vs Dynamism">
          <div className="h-64 font-mono text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartDataDyn} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="dynamism" stroke="#888" label={{ value: 'Dynamism', position: 'insideBottomRight', offset: -10, fill: '#888' }} />
                <YAxis stroke="#888" label={{ value: 'Disruption', angle: -90, position: 'insideLeft', fill: '#888' }} />
                <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                <Legend />
                {Object.keys(colors).map(strat => (
                  <Line key={strat} type="monotone" dataKey={`${strat}_disr`} name={labels[strat as keyof typeof labels]} stroke={colors[strat as keyof typeof colors]} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Quality vs Compute Time">
          <div className="h-64 font-mono text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" dataKey="time" name="Compute Time" stroke="#888" scale="log" domain={['auto', 'auto']} label={{ value: 'Compute Time (s, log)', position: 'bottom', fill: '#888', offset: 0 }} />
                <YAxis type="number" dataKey="dist" name="Total Distance" stroke="#888" label={{ value: 'Total Distance', angle: -90, position: 'left', fill: '#888', offset: -10 }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                <Legend />
                {Object.keys(colors).map(strat => (
                  <Scatter key={strat} name={labels[strat as keyof typeof labels]} data={scatterData.filter((d:any) => d.strategy === strat)} fill={colors[strat as keyof typeof colors]} />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="Aggregated Statistics (n=3)">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-sm border-collapse">
            <thead>
              <tr className="border-b border-[#333] text-[var(--accent-2)]">
                <th className="py-2 pr-4">Dynamism</th>
                <th className="py-2 pr-4">Strategy</th>
                <th className="py-2 pr-4 text-right">Mean Distance</th>
                <th className="py-2 pr-4 text-right">SD Distance</th>
              </tr>
            </thead>
            <tbody>
              {data.aggregated.map((a: any, i: number) => (
                <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                  <td className="py-2 pr-4">{a.dynamism}</td>
                  <td className="py-2 pr-4 text-gray-300">{labels[a.strategy as keyof typeof labels]}</td>
                  <td className="py-2 pr-4 text-right">{a.mean_distance.toFixed(2)}</td>
                  <td className="py-2 pr-4 text-right">{a.sd_distance.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Paired Differences (Pooled)">
        <p className="text-sm font-sans text-gray-400 mb-4 italic">n is small (3 seeds per cell), so tests have low power; treat as descriptive.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-sm border-collapse">
            <thead>
              <tr className="border-b border-[#333] text-[var(--accent-2)]">
                <th className="py-2 pr-4">Comparison</th>
                <th className="py-2 pr-4 text-right">Mean Diff</th>
                <th className="py-2 pr-4 text-right">95% CI</th>
                <th className="py-2 pr-4 text-right">Wilcoxon p (Holm)</th>
                <th className="py-2 pr-4 text-center">Significant?</th>
              </tr>
            </thead>
            <tbody>
              {data.paired_stats.pairwise.map((p: any, i: number) => (
                <tr key={i} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                  <td className="py-2 pr-4 text-gray-300">{p.compare}</td>
                  <td className="py-2 pr-4 text-right">{p.mean_diff.toFixed(2)}</td>
                  <td className="py-2 pr-4 text-right">[{p.ci_95[0].toFixed(2)}, {p.ci_95[1].toFixed(2)}]</td>
                  <td className="py-2 pr-4 text-right">{p.p_value.toFixed(4)}</td>
                  <td className="py-2 pr-4 text-center">
                    {p.significant_holm ? <span className="text-[var(--accent-2)]">Yes</span> : <span className="text-gray-500">No</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

const Compare = () => {
  const [data, setData] = useState<any>(null);
  useEffect(() => { fetch('/demo/results.json').then(r => r.json()).then(setData); }, []);
  
  if (!data) return <div className="p-6 font-sans text-gray-400">Loading...</div>;

  const getMet = (strat: string, metric: string) => {
    const items = data.aggregated.filter((a:any) => a.strategy === strat);
    if (!items.length) return 'N/A';
    const sum = items.reduce((s:number,a:any) => {
        if (metric === 'dist') return s + a.mean_distance;
        // per_run needed for others? Wait, data.aggregated only has distance?
        // Ah, I only exported distance in aggregated!
        return s;
    }, 0);
    return (sum / items.length).toFixed(2);
  };

  const getPr = (strat: string, metric: string) => {
      const items = data.per_run.filter((a:any) => a.strategy === strat);
      if(!items.length) return 'N/A';
      const sum = items.reduce((s:number, a:any) => {
          if (metric === 'time') return s + a.metrics.total_time_s;
          if (metric === 'evals') return s + a.metrics.evaluations;
          if (metric === 'disr') return s + a.metrics.route_disruption;
          return s;
      }, 0);
      return (sum / items.length).toFixed(2);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto font-sans">
      <h1 className="text-3xl font-bold text-[var(--accent-1)] mb-6">Compare Strategies</h1>
      <Card>
        <table className="w-full text-left font-mono text-sm">
           <thead>
             <tr className="border-b border-[#333] text-[var(--accent-2)]">
               <th className="py-3">Metric (Global Mean)</th>
               <th>Greedy</th>
               <th>2-Opt*</th>
               <th>Tabu Search</th>
             </tr>
           </thead>
           <tbody>
             <tr>
               <td className="py-2">Mean Distance</td>
               <td>{getMet('greedy_insertion', 'dist')}</td>
               <td>{getMet('insertion_2opt_star', 'dist')}</td>
               <td>{getMet('tabu_search', 'dist')}</td>
             </tr>
             <tr>
               <td className="py-2">Mean Compute Time (s)</td>
               <td>{getPr('greedy_insertion', 'time')}</td>
               <td>{getPr('insertion_2opt_star', 'time')}</td>
               <td>{getPr('tabu_search', 'time')}</td>
             </tr>
             <tr>
               <td className="py-2">Mean Evaluations</td>
               <td>{getPr('greedy_insertion', 'evals')}</td>
               <td>{getPr('insertion_2opt_star', 'evals')}</td>
               <td>{getPr('tabu_search', 'evals')}</td>
             </tr>
             <tr>
               <td className="py-2">Mean Disruption</td>
               <td>{getPr('greedy_insertion', 'disr')}</td>
               <td>{getPr('insertion_2opt_star', 'disr')}</td>
               <td>{getPr('tabu_search', 'disr')}</td>
             </tr>
           </tbody>
        </table>
      </Card>
      <RequiresBackend />
    </div>
  );
};

const Methodology = () => (
  <div className="p-6 max-w-3xl mx-auto font-sans">
    <h1 className="text-3xl font-bold text-[var(--accent-1)] mb-6">Methodology</h1>
    <Card>
      <p className="text-gray-300 mb-4">This prototype compares three DVRP strategies across varying degrees of dynamism (0.1, 0.4, 0.8).</p>
      <ul className="list-disc pl-5 text-gray-300 space-y-2 mb-6">
        <li><strong>Greedy Insertion:</strong> Cheapest valid insertion per arrival.</li>
        <li><strong>2-Opt*:</strong> Greedy insertion followed by a tail-exchange local search.</li>
        <li><strong>Tabu Search:</strong> Limited search (relocate, swap, 2-opt*) with a hard evaluation budget (200).</li>
      </ul>
      <p className="text-gray-300 italic mb-2">Note: The adaptive selector is marked as future work.</p>
    </Card>
  </div>
);

const App = () => (
  <div className="min-h-screen bg-[#0B0F0A] text-[#F2FFE9]">
    <Banner />
    <Nav />
    <Routes>
      <Route path="/" element={<Navigate to="/results" replace />} />
      <Route path="/overview" element={<Overview />} />
      <Route path="/results" element={<Results />} />
      <Route path="/compare" element={<Compare />} />
      <Route path="/replay" element={<RequiresBackend />} />
      <Route path="/lab" element={<RequiresBackend />} />
      <Route path="/experiments" element={<RequiresBackend />} />
      <Route path="/methodology" element={<Methodology />} />
      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Routes>
  </div>
);

export default App;
