import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import AddAssetModal from '../components/modals/AddAssetModal';
import PortfolioItemDetail from './PortfolioItemDetail';

export default function PortfolioDetail({ portfolioId, portfolioCurrency, onBack }) {
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
      if (!response.ok) throw new Error("Fehler beim Laden der Details");
      const data = await response.json();
      
      let items = Array.isArray(data) ? data : [];

      // --- ALPHABETISCHE SORTIERUNG NACH SYMBOL ---
      items.sort((a, b) => {
        const symbolA = (a.asset?.symbol || "").toUpperCase();
        const symbolB = (b.asset?.symbol || "").toUpperCase();
        return symbolA.localeCompare(symbolB);
      });

      setPortfolioItems(items);
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

  const totals = portfolioItems.reduce((acc, item) => {
    const qty = parseFloat(item.quantity || 0);
    const avgCost = parseFloat(item.avg_cost_price || 0);
    const currentPrice = parseFloat(item.asset?.current_price || 0);
    
    acc.totalEntry += qty * avgCost;
    acc.totalMarket += qty * currentPrice;
    return acc;
  }, { totalEntry: 0, totalMarket: 0 });

  const totalProfitLoss = totals.totalMarket - totals.totalEntry;
  const totalProfitLossPct = totals.totalEntry > 0 
    ? (totalProfitLoss / totals.totalEntry) * 100 
    : 0;

  const getHeaderColorClass = (value) => {
    if (value > 0.01) return 'text-emerald-500';
    if (value < -0.01) return 'text-rose-500';
    return 'text-slate-900';
  };

  const getHeaderBadgeClass = (value) => {
    if (value > 0.01) return 'bg-emerald-50 text-emerald-600';
    if (value < -0.01) return 'bg-rose-50 text-rose-600';
    return 'bg-slate-100 text-slate-600';
  };

  if (selectedItemId) {
    return (
      <PortfolioItemDetail 
        portfolioId={portfolioId} 
        itemId={selectedItemId} 
        portfolioCurrency={portfolioCurrency}
        onBack={(msg) => {
          setSelectedItemId(null);
          fetchDetails();
          if (msg) showToast(msg);
        }} 
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-in fade-in duration-500 relative text-slate-900">
      
      {toast && (
        <div className={`fixed top-10 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-2xl shadow-2xl font-bold text-white animate-in fade-in zoom-in ${toast.type === 'error' ? 'bg-rose-500' : 'bg-emerald-500'}`}>
          {toast.type === 'success' ? '✅ ' : '❌ '} {toast.message}
        </div>
      )}

      <button onClick={onBack} className="mb-6 text-indigo-600 font-bold flex items-center gap-2 hover:translate-x-1 transition-transform uppercase text-xs tracking-widest">
        <span>←</span> Zurück zur Übersicht
      </button>

      <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 mb-8">
        <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-8">Portfolio Performance</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-end">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Aktueller Depotwert</span>
            <div className="text-4xl font-black text-indigo-600 tabular-nums">
              {formatCurrency(totals.totalMarket, portfolioCurrency)}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Investiertes Kapital</span>
            <div className="text-2xl font-bold text-slate-700 tabular-nums">
              {formatCurrency(totals.totalEntry, portfolioCurrency)}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Gesamtrendite (G/V)</span>
            <div className={`text-2xl font-black tabular-nums flex items-baseline gap-2 ${getHeaderColorClass(totalProfitLoss)}`}>
              <span>{totalProfitLoss > 0.01 ? '+' : ''}{formatCurrency(totalProfitLoss, portfolioCurrency)}</span>
              <span className={`text-xs px-2 py-1 rounded-lg font-bold ${getHeaderBadgeClass(totalProfitLoss)}`}>
                {totalProfitLoss > 0.01 ? '+' : ''}{totalProfitLossPct.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-slate-800">Übersicht Assets</h3>
        <button 
          onClick={() => setShowAddModal(true)} 
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg transition-all active:scale-95 text-sm"
        >
          + Asset hinzufügen
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 text-[10px] uppercase font-black tracking-wider">
              <tr>
                <th className="px-6 py-4">Asset</th>
                <th className="px-4 py-4 text-right">Menge</th>
                <th className="px-4 py-4 text-right">Einstiegswert</th>
                <th className="px-4 py-4 text-right">Marktwert</th>
                <th className="px-4 py-4 text-right">Kurs</th>
                <th className="px-6 py-4 text-right">G/V (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {isLoading ? (
                <tr>
                  <td colSpan="6" className="py-20 text-center text-slate-400 font-medium">Lade Assets...</td>
                </tr>
              ) : portfolioItems.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-20 text-center text-slate-400 font-medium">Noch keine Assets vorhanden.</td>
                </tr>
              ) : (
                portfolioItems.map((item) => {
                  const qty = parseFloat(item.quantity || 0);
                  const avgCost = parseFloat(item.avg_cost_price || 0);
                  const currentPrice = parseFloat(item.asset?.current_price || 0);
                  
                  const entryValue = qty * avgCost;
                  const marketValue = qty * currentPrice;
                  const profitLoss = marketValue - entryValue;
                  const profitLossPct = entryValue > 0 ? (profitLoss / entryValue) * 100 : 0;

                  let rowColorClass = 'text-slate-900';
                  if (profitLoss > 0.001) rowColorClass = 'text-emerald-500';
                  if (profitLoss < -0.001) rowColorClass = 'text-rose-500';

                  return (
                    <tr key={item.id} onClick={() => setSelectedItemId(item.id)} className="hover:bg-slate-50/50 transition-colors cursor-pointer group">
                      <td className="px-6 py-5">
                        <div className="font-black text-slate-900 group-hover:text-indigo-600 transition-colors">
                          {item.asset?.symbol}
                        </div>
                        <div className="text-[10px] text-slate-400 font-bold truncate max-w-[150px]">
                          {item.asset?.name}
                        </div>
                      </td>
                      <td className="px-4 py-5 tabular-nums text-right font-medium text-slate-600">
                        {qty.toLocaleString()}
                      </td>
                      <td className="px-4 py-5 tabular-nums text-right text-slate-500 font-medium text-xs">
                        {formatCurrency(entryValue, portfolioCurrency)}
                      </td>
                      <td className="px-4 py-5 tabular-nums text-right font-black text-slate-900">
                        {formatCurrency(marketValue, portfolioCurrency)}
                      </td>
                      <td className="px-4 py-5 tabular-nums text-right text-[10px] text-slate-400 font-bold">
                        {formatCurrency(currentPrice, portfolioCurrency)}
                      </td>
                      <td className={`px-6 py-5 tabular-nums text-right font-black ${rowColorClass}`}>
                        <div className="text-sm">
                          {profitLoss > 0.001 ? '+' : ''}{formatCurrency(profitLoss, portfolioCurrency)}
                        </div>
                        <div className="text-[10px] opacity-80">
                          {profitLoss > 0.001 ? '+' : ''}{profitLossPct.toFixed(2)}%
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showAddModal && (
        <AddAssetModal 
          portfolioId={portfolioId}
          portfolioCurrency={portfolioCurrency}
          onClose={() => setShowAddModal(false)} 
          onRefresh={fetchDetails} 
        />
      )}
    </div>
  );
}