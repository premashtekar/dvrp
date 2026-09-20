// src/App.tsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Overview from './pages/Overview';
import ScenarioLab from './pages/ScenarioLab';
import SimulationReplay from './pages/SimulationReplay';
import NotImplemented from './pages/NotImplemented';

const App: React.FC = () => (
  <Routes>
    <Route path="/" element={<Navigate to="/overview" replace />} />
    <Route path="/overview" element={<Overview />} />
    <Route path="/lab" element={<ScenarioLab />} />
    <Route path="/replay/:runId" element={<SimulationReplay />} />
    <Route path="/compare" element={<NotImplemented pageName="Compare" />} />
    <Route path="/experiments" element={<NotImplemented pageName="Experiments" />} />
    <Route path="/results" element={<NotImplemented pageName="Results" />} />
    <Route path="/methodology" element={<NotImplemented pageName="Methodology" />} />
  </Routes>
);

export default App;
