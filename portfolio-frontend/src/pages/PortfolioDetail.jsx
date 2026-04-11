import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import AddAssetModal from '../components/modals/AddAssetModal';
import PortfolioItemDetail from './PortfolioItemDetail';

export default function PortfolioDetail({ portfolioId, onBack }) {
  const [portfolioItems, setPortfolioItems] = useState([]);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [toast, setToast] = useState(null);

  const fetchDetails = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio_item/${portfolioId}`, {
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }
      });
      if (!response.ok) throw new Error("Fehler");
      const data = await response.json();
      setPortfolioItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [portfolioId]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  if (selectedItemId) {
    return (
      <PortfolioItemDetail 
        portfolioId={portfolioId} 
        itemId={selectedItemId} 
        onBack={(msg) => {
          setSelectedItemId(null);
          fetchDetails();
          if (msg) showToast(msg);
        }} 
      />
    );
  }

  const totalValue = portfolioItems.reduce((sum, item) => sum + (parseFloat(item.quantity) * parseFloat(item.avg_cost_price)), 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-in fade-in duration-500 relative">
      
      {/* Toast-Anzeige (jetzt hier in der Liste) */}
      {toast && (
        <div className={`fixed top-10 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-2xl shadow-2xl font-bold text-white animate-in fade-in zoom-in ${toast.type === 'error' ? 'bg-rose-500' : 'bg-emerald-500'}`}>
          {toast.type === 'success' ? '✅ ' : '❌ '} {toast.message}
        </div>
      )}

      <button onClick={onBack} className="mb-6 text-indigo-600 font-bold flex items-center gap-2 hover:translate-x-1 transition-transform">
        <span>←</span> Zurück zur Übersicht
      </button>

      <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 mb-8">
        <h2 className="text-3xl font-black text-slate-900 tracking-tight">Portfolio Assets</h2>
        <div className="mt-8">
          <span className="text-xs text-slate-400 font-black uppercase tracking-widest">Gesamtwert</span>
          <div className="text-4xl font-black text-indigo-600 tabular-nums">{formatCurrency(totalValue)}</div>
        </div>
      </div>

      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-slate-800">Assets</h3>
        <button onClick={() => setShowAddModal(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg transition-all active:scale-95">
          + Asset hinzufügen
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 text-[11px] uppercase font-black tracking-wider">
            <tr>
              <th className="px-8 py-4">Asset</th>
              <th className="px-6 py-4 text-right">Menge</th>
              <th className="px-6 py-4 text-right">Wert</th>
              <th className="px-6 py-4 text-center">Aktion</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {portfolioItems.map((item) => (
              <tr key={item.id} onClick={() => setSelectedItemId(item.id)} className="hover:bg-slate-50/50 transition-colors cursor-pointer group">
                <td className="px-8 py-5 font-bold text-slate-900 group-hover:text-indigo-600">{item.asset?.name}</td>
                <td className="px-6 py-5 tabular-nums text-right font-medium">{Number(item.quantity).toLocaleString()}</td>
                <td className="px-6 py-5 font-black text-slate-900 tabular-nums text-right">
                  {formatCurrency(parseFloat(item.quantity) * parseFloat(item.avg_cost_price))}
                </td>
                <td className="px-6 py-5 text-center">
                   <span className="text-indigo-600 font-bold text-xs bg-indigo-50 px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">Details →</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddModal && <AddAssetModal portfolioId={portfolioId} onClose={() => setShowAddModal(false)} onRefresh={fetchDetails} />}
    </div>
  );
}