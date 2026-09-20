// src/pages/NotImplemented.tsx
import React from 'react';

interface Props {
  pageName: string;
}

const NotImplemented: React.FC<Props> = ({ pageName }) => (
  <div className="p-8 text-center">
    <h2 className="text-2xl font-bold mb-4">{pageName} – Not Implemented</h2>
    <p className="text-gray-600">This page is not part of the fast‑track build.</p>
  </div>
);

export default NotImplemented;
