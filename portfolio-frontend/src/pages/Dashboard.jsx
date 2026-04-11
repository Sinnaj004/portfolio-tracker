import React, { useState, useEffect } from 'react';
import StatCard from '../components/dashboard/StatCard';
import CreatePortfolioModal from '../components/modals/CreatePortfolioModal';
import DeleteConfirmModal from '../components/modals/DeleteConfirmModal';
import PortfolioDetail from './PortfolioDetail';
import Navbar from '../components/dashboard/Navbar'; // Import der neuen Navbar
import { formatCurrency } from '../utils/formatters';

export default function Dashboard({ onLogout }) {
  // --- States ---
  const [portfolios, setPortfolios] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Navigation State
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);

  // Modal States
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [portfolioToDelete, setPortfolioToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // --- API: Portfolios laden ---
  const fetchPortfolios = async () => {
    setIsLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio/`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        if (response.status === 401) onLogout();
        throw new Error("Fehler beim Laden der Portfolios");
      }

      const data = await response.json();
      setPortfolios(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // --- API: Portfolio löschen ---
  const handleConfirmDelete = async () => {
    if (!portfolioToDelete) return;
    
    setIsDeleting(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio/${portfolioToDelete.id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (!response.ok) throw new Error("Löschen fehlgeschlagen.");

      setPortfolios(prev => prev.filter(p => p.id !== portfolioToDelete.id));
      setPortfolioToDelete(null);
    } catch (err) {
      alert(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const totalNetWorth = portfolios.reduce((sum, p) => sum + (p.total_value || 0), 0);

  // --- BEDINGTES RENDERING: DETAILANSICHT ---
  if (selectedPortfolioId) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar onLogout={onLogout} /> {/* Navbar bleibt auch in Details oben */}
        <PortfolioDetail 
          portfolioId={selectedPortfolioId} 
          onBack={() => {
            setSelectedPortfolioId(null);
            fetchPortfolios();
          }} 
        />
      </div>
    );
  }

  // --- NORMALES RENDERING: ÜBERSICHT ---
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* 1. Die neue Navbar ersetzt den alten Header */}
      <Navbar onLogout={onLogout} />

      <main className="max-w-7xl mx-auto px-4 py-10">
        <div className="mb-10">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Deine Übersicht</h2>
          <p className="text-slate-500 mt-1 font-medium">Verwalte deine Portfolios</p>
        </div>

        {error && (
          <div className="bg-rose-50 text-rose-600 p-4 rounded-2xl mb-8 border border-rose-100 flex justify-between items-center">
            <span className="font-semibold">{error}</span>
            <button onClick={fetchPortfolios} className="underline font-bold text-sm">Erneut versuchen</button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <StatCard title="Gesamtvermögen" value={totalNetWorth} />
          <StatCard title="Portfolios" value={portfolios.length} isCurrency={false} />
          <StatCard title="Status" value="Live" isCurrency={false} />
        </div>

        <div className="flex justify-between items-center mb-8">
          <h3 className="text-xl font-bold text-slate-800">Meine Portfolios</h3>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-xl text-sm font-bold shadow-lg transition-all active:scale-95"
          >
            + Portfolio hinzufügen
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            <div className="col-span-full py-20 text-center">
              <div className="animate-spin h-10 w-10 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-slate-400">Lade Portfolios...</p>
            </div>
          ) : portfolios.length === 0 ? (
            <div className="col-span-full bg-white p-12 rounded-3xl border-2 border-dashed border-slate-200 text-center">
              <p className="text-slate-500 font-medium mb-4 text-lg">Keine Portfolios vorhanden.</p>
              <button onClick={() => setShowCreateModal(true)} className="text-indigo-600 font-bold hover:underline">Erstelle dein erstes Portfolio</button>
            </div>
          ) : (
            portfolios.map((p) => (
              <div 
                key={p.id} 
                onClick={() => setSelectedPortfolioId(p.id)} 
                className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all cursor-pointer group relative overflow-hidden"
              >
                <button 
                  onClick={(e) => {
                    e.stopPropagation(); 
                    setPortfolioToDelete({ id: p.id, name: p.name });
                  }}
                  className="absolute top-4 right-4 p-2 text-slate-300 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all opacity-0 group-hover:opacity-100 z-10"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>

                <div className="bg-indigo-50 text-indigo-600 w-12 h-12 rounded-xl flex items-center justify-center mb-6 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                </div>
                
                <h4 className="text-lg font-bold text-slate-900 mb-1">{p.name}</h4>
                <p className="text-sm text-slate-500 line-clamp-2 h-10 mb-6">{p.description || 'Keine Beschreibung.'}</p>
                
                <div className="pt-5 border-t border-slate-50 flex justify-between items-end">
                  <div>
                    <span className="text-xs text-slate-400 font-bold uppercase">Wert</span>
                    <p className="text-xl font-black text-slate-800">{formatCurrency(p.total_value || 0)}</p>
                  </div>
                  <span className="text-indigo-600 font-bold text-sm group-hover:translate-x-1 transition-transform">Details →</span>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {showCreateModal && <CreatePortfolioModal onClose={() => setShowCreateModal(false)} onRefresh={fetchPortfolios} />}
      {portfolioToDelete && <DeleteConfirmModal title={portfolioToDelete.name} isLoading={isDeleting} onClose={() => setPortfolioToDelete(null)} onConfirm={handleConfirmDelete} />}
    </div>
  );
}