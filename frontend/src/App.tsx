import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ContractDetail from './pages/ContractDetail';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            AI Contract Auditor
          </h1>
          <p className="text-sm text-gray-500">
            Automated contract analysis and validation
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/contracts/:id" element={<ContractDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
