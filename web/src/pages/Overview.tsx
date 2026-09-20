// src/pages/Overview.tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface RunInfo {
  id: string;
  scenario_id: string;
  strategy: string;
  status: string;
  created_at: string;
}

const Overview: React.FC = () => {
  const [runs, setRuns] = useState<RunInfo[]>([]);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const resp = await axios.get<RunInfo[]>('/api/v1/runs?limit=10');
        setRuns(resp.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchRuns();
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Overview</h1>
      <p className="mb-2">Recent simulation runs (live mode).</p>
      <table className="min-w-full bg-white border">
        <thead>
          <tr>
            <th className="px-4 py-2 border">Run ID</th>
            <th className="px-4 py-2 border">Strategy</th>
            <th className="px-4 py-2 border">Status</th>
            <th className="px-4 py-2 border">Created</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td className="px-4 py-2 border break-all">{run.id}</td>
              <td className="px-4 py-2 border">{run.strategy}</td>
              <td className="px-4 py-2 border">{run.status}</td>
              <td className="px-4 py-2 border">{new Date(run.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Overview;
