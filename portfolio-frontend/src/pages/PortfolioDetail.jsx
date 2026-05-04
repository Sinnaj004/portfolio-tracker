import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import AddAssetModal from '../components/modals/AddAssetModal';
import PortfolioItemDetail from './PortfolioItemDetail';
import Portfoliochart_ApexChart from '../components/charts/Portfoliochart_ApexChart';
import TransactionHistoryTable from '../components/PortfolioDetail/TransactionHistoryTable';
import PortfolioAnalysis from '../components/PortfolioDetail/PortfolioAnalyses'; 

export default function PortfolioDetail({ portfolioId, portfolioCurrency, onBack }) {
  const [portfolioItems, setPortfolioItems] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [toast, setToast] = useState(null);
  const [days, setDays] = useState(30);
  
  // ERWEITERTE TAB-LOGIK
  const [activeTab, setActiveTab] = useState('assets'); // 'assets', 'history', 'analysis'

  const fetchDetails = async () => {
    const token = localStorage.getItem('token');
    const apiUrl = `/api/v1`;

    try {
      setIsLoading(true);
      const itemsRes = await fetch(`${apiUrl}/portfolio_item/${portfolioId}`, {
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }
      });
      if (!itemsRes.ok) throw new Error("Fehler beim Laden der Assets");
      const itemsData = await itemsRes.json();
      
      let items = Array.isArray(itemsData) ? itemsData : [];
      items.sort((a, b) => (a.asset?.symbol || "").localeCompare(b.asset?.symbol || ""));
      setPortfolioItems(items);

      const perfRes = await fetch(`${apiUrl}/portfolio/${portfolioId}/performance?days=${days}`, {
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }
      });
      if (perfRes.ok) {
        const perfData = await perfRes.json();
        setPerformanceData(perfData);
      }
    } catch (err) {
      console.error(err);
      showToast("Daten konnten nicht geladen werden", "error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [portfolioId, days]);

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
  const totalProfitLossPct = totals.totalEntry > 0 ? (totalProfitLoss / totals.totalEntry) * 100 : 0;

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

      {/* --- CHART SECTION (Immer sichtbar) --- */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 mb-8">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">Portfolio Analyse</h2>
            <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Zeitverlauf & Rendite</p>
          </div>
          <div className="flex bg-slate-100 p-1 rounded-xl">
            {[7, 30, 90, 365].map((d) => (
              <button key={d} onClick={() => setDays(d)} className={`px-4 py-1.5 rounded-lg text-xs font-black transition-all ${days === d ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}>
                {d === 365 ? '1J' : `${d}D`}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-10 w-full">
          {isLoading ? (
            <div className="h-[350px] flex items-center justify-center bg-slate-50 rounded-2xl animate-pulse text-slate-400 text-sm font-bold">Lade Chart-Daten...</div>
          ) : (
            <Portfoliochart_ApexChart performanceData={performanceData} portfolioCurrency={portfolioCurrency} />
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-end border-t border-slate-100 pt-8">
          <div>
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Depotwert</span>
            <div className="text-4xl font-black text-indigo-600 tabular-nums">{formatCurrency(totals.totalMarket, portfolioCurrency)}</div>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Investiert</span>
            <div className="text-2xl font-bold text-slate-700 tabular-nums">{formatCurrency(totals.totalEntry, portfolioCurrency)}</div>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Rendite</span>
            <div className={`text-2xl font-black tabular-nums flex items-baseline gap-2 ${totalProfitLoss >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
              {formatCurrency(totalProfitLoss, portfolioCurrency)}
              <span className={`text-xs px-2 py-1 rounded-lg font-bold ${totalProfitLoss >= 0 ? 'bg-emerald-50' : 'bg-rose-50'}`}>
                {totalProfitLossPct.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* --- TAB NAVIGATION --- */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-100">
        <div className="flex gap-10">
          {[
            { id: 'assets', label: 'Einzelwerte' },
            { id: 'history', label: 'Aktivität' },
            { id: 'analysis', label: 'Diversifikation' }
          ].map((tab) => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 text-xs font-black uppercase tracking-widest transition-all relative ${activeTab === tab.id ? 'text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
            >
              {tab.label}
              {activeTab === tab.id && <div className="absolute bottom-0 left-0 w-full h-1 bg-indigo-600 rounded-full animate-in slide-in-from-left-2" />}
            </button>
          ))}
        </div>
        
        {activeTab === 'assets' && (
          <button onClick={() => setShowAddModal(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg mb-4 text-xs uppercase tracking-widest transition-all active:scale-95">
            + Asset hinzufügen
          </button>
        )}
      </div>

      {/* --- CONTENT BEDINGT RENDERN --- */}
      <div className="transition-all duration-300">
        {activeTab === 'assets' && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden animate-in fade-in slide-in-from-bottom-2">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 text-[10px] uppercase font-black tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Asset</th>
                    <th className="px-4 py-4 text-right">Menge</th>
                    <th className="px-4 py-4 text-right">Einstieg</th>
                    <th className="px-4 py-4 text-right">Marktwert</th>
                    <th className="px-6 py-4 text-right">G/V (%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {portfolioItems.map((item) => {
                    const qty = parseFloat(item.quantity || 0);
                    const marketVal = qty * parseFloat(item.asset?.current_price || 0);
                    const entryVal = qty * parseFloat(item.avg_cost_price || 0);
                    const diff = marketVal - entryVal;

                    return (
                      <tr key={item.id} onClick={() => setSelectedItemId(item.id)} className="hover:bg-slate-50/50 transition-colors cursor-pointer group">
                        <td className="px-6 py-5">
                          <div className="font-black text-slate-900 group-hover:text-indigo-600">{item.asset?.symbol}</div>
                          <div className="text-[10px] text-slate-400 font-bold">{item.asset?.name}</div>
                        </td>
                        <td className="px-4 py-5 tabular-nums text-right font-medium text-slate-600">{qty.toLocaleString()}</td>
                        <td className="px-4 py-5 tabular-nums text-right text-slate-500 text-xs">{formatCurrency(entryVal, portfolioCurrency)}</td>
                        <td className="px-4 py-5 tabular-nums text-right font-black text-slate-900">{formatCurrency(marketVal, portfolioCurrency)}</td>
                        <td className={`px-6 py-5 tabular-nums text-right font-black ${diff >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                          <div className="text-sm">{formatCurrency(diff, portfolioCurrency)}</div>
                          <div className="text-[10px] opacity-80">{(entryVal > 0 ? (diff/entryVal)*100 : 0).toFixed(2)}%</div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="animate-in fade-in slide-in-from-bottom-2">
            <TransactionHistoryTable portfolioId={portfolioId} portfolioCurrency={portfolioCurrency} />
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="animate-in fade-in slide-in-from-bottom-2">
            <PortfolioAnalysis 
              portfolioItems={portfolioItems} 
              portfolioCurrency={portfolioCurrency} 
            />
          </div>
        )}
      </div>

      {showAddModal && (
        <AddAssetModal portfolioId={portfolioId} portfolioCurrency={portfolioCurrency} onClose={() => setShowAddModal(false)} onRefresh={fetchDetails} />
      )}
    </div>
  );
}