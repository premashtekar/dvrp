// src/pages/ScenarioLab.tsx
import React, { useState } from 'react';
import axios from 'axios';

const ScenarioLab: React.FC = () => {
  const [form, setForm] = useState({
    customers: 5,
    vehicles: 2,
    capacity: 10,
    dynamism: 0.4,
    seed: 42,
    map_size: 100,
    horizon: 100,
  });
  const [scenarioId, setScenarioId] = useState<string>('');
  const [runId, setRunId] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const backendAvailable = !!process.env.VITE_API_URL;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: Number(value) }));
  };

  const createScenario = async () => {
    try {
      const resp = await axios.post('/api/v1/scenarios', form);
      setScenarioId(resp.data.id);
      setMessage('Scenario created.');
    } catch (err) {
      console.error(err);
      setMessage('Backend required to create scenario.');
    }
  };

  const startRun = async (strategy: string) => {
    if (!scenarioId) {
      setMessage('Create a scenario first.');
      return;
    }
    try {
      const resp = await axios.post('/api/v1/simulations', {
        scenario_id: scenarioId,
        strategy,
        budget: {},
      });
      setRunId(resp.data.run_id);
      setMessage(`Run started (strategy ${strategy}).`);
    } catch (err) {
      console.error(err);
      setMessage('Backend required to start run.');
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Scenario Lab</h1>
      {!backendAvailable && (
        <p className="text-red-600 mb-2">Backend unavailable – this page works only in live mode.</p>
      )}
      <div className="space-y-2">
        {Object.entries(form).map(([key, val]) => (
          <div key={key} className="flex items-center">
            <label className="w-32 capitalize" htmlFor={key}>{key.replace('_', ' ')}</label>
            <input
              id={key}
              name={key}
              type="number"
              value={val}
              onChange={handleChange}
              className="border rounded px-2 py-1 flex-1"
            />
          </div>
        ))}
      </div>
      <button
        className="mt-4 bg-mint text-bg px-4 py-2 rounded"
        onClick={createScenario}
        disabled={!backendAvailable}
      >
        Create Scenario
      </button>
      {scenarioId && (
        <div className="mt-4">
          <p>Scenario ID: <span className="break-all font-mono">{scenarioId}</span></p>
          <button
            className="mr-2 bg-lime text-bg px-3 py-1 rounded"
            onClick={() => startRun('greedy_insertion')}
          >
            Run Greedy Insertion (A)
          </button>
          <button
            className="bg-mint text-bg px-3 py-1 rounded"
            onClick={() => startRun('insertion_2opt_star')}
          >
            Run 2‑opt* (B)
          </button>
        </div>
      )}
      {runId && (
        <div className="mt-4">
          <p>Run ID: <span className="break-all font-mono">{runId}</span></p>
          <a href={`/replay/${runId}`} className="text-blue-400 underline">Go to Replay</a>
        </div>
      )}
      {message && <p className="mt-2 text-gray-700">{message}</p>
      }
    </div>
  );
};

export default ScenarioLab;
