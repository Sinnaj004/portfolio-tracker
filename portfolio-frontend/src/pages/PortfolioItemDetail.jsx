import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import DeleteConfirmModal from '../components/modals/DeleteConfirmModal';

export default function PortfolioItemDetail({ portfolioId, itemId, portfolioCurrency, onBack }) {
  const [item, setItem] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [showSellForm, setShowSellForm] = useState(false);
  const [sellQuantity, setSellQuantity] = useState('');
  const [sellPrice, setSellPrice] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [sellSuccess, setSellSuccess] = useState(false);

  useEffect(() => {
    fetchItem();
  }, [portfolioId, itemId]);

  const fetchItem = async () => {
    const token = localStorage.getItem('token');
    setIsLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio_item/${portfolioId}/items/${itemId}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Fehler beim Laden");
      const data = await response.json();
      setItem(data);
    } catch (err) {
      console.error("Fetch Fehler:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSell = async (e) => {
    e.preventDefault();
    setIsActionLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio_item/${portfolioId}/items/${itemId}/sell`, { 
        method: 'POST',
        headers: { 
          "Authorization": `Bearer ${token}`, 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ 
          quantity: parseFloat(sellQuantity),
          sale_price: sellPrice ? parseFloat(sellPrice) : null 
        })
      });

      if (response.ok) {
        // Wir rufen onBack für JEDEN erfolgreichen Verkauf auf
        // Die Nachricht unterscheidet zwischen Teil- und Vollverkauf
        const isFullSale = response.status === 204; 
        
        onBack(isFullSale ? "Position vollständig verkauft" : "Teilverkauf erfolgreich verbucht");
      }
    } catch (err) { 
      console.error(err); 
      // Optional: Hier könntest du einen Fehler-Toast einbauen, falls der Verkauf fehlschlägt
    } finally { 
      setIsActionLoading(false); 
    }
  };

  const handleDelete = async () => {
    setIsActionLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio_item/${portfolioId}/items/${itemId}`, { 
        method: 'DELETE',
        headers: { "Authorization": `Bearer ${token}` } 
      });
      if (response.status === 204 || response.ok) {
        onBack("Position erfolgreich gelöscht");
      }
    } catch (err) { 
      console.error("Lösch-Fehler:", err); 
    } finally { 
      setIsActionLoading(false); 
      setShowDeleteConfirm(false);
    }
  };

  if (isLoading) return <div className="p-20 text-center font-bold text-slate-500">Lade Daten...</div>;
  if (!item) return <div className="p-20 text-center">Nicht gefunden.</div>;

  const qty = parseFloat(item.quantity);
  const avgPrice = parseFloat(item.avg_cost_price);

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-in slide-in-from-right duration-300 relative">
      
        <style>{`
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
          -webkit-appearance: none;
          margin: 0;
        }
        input[type=number] {
          -moz-appearance: textfield;
        }
      `}</style>
      {/* SUCCESS NOTIFICATION */}
      {sellSuccess && (
        <div className="fixed top-24 left-1/2 -translate-x-1/2 z-[150] bg-slate-900 text-white px-8 py-4 rounded-2xl shadow-2xl flex items-center gap-4 border-b-4 border-indigo-500 animate-in fade-in zoom-in duration-300">
          <div className="w-6 h-6 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600 text-[10px] font-black">✓</div>
          <span className="font-black uppercase tracking-widest text-xs">Teilverkauf verbucht</span>
        </div>
      )}

      {/* NAVIGATION & ACTIONS */}
      <div className="flex justify-between items-center mb-8">
        <button onClick={() => onBack()} className="text-indigo-600 font-bold flex items-center gap-2 transition-transform hover:-translate-x-1 uppercase text-xs tracking-widest">
          ← Zurück
        </button>
        <div className="flex gap-3">
          <button 
            onClick={() => setShowSellForm(!showSellForm)} 
            className={`px-5 py-2.5 rounded-xl font-bold uppercase text-[10px] tracking-widest transition-all ${showSellForm ? 'bg-amber-500 text-white shadow-lg shadow-amber-200' : 'bg-amber-50 text-amber-600 hover:bg-amber-100'}`}
          >
            {showSellForm ? 'Schließen' : 'Verkauf'}
          </button>
          <button 
            onClick={() => setShowDeleteConfirm(true)} 
            className="bg-rose-50 text-rose-600 px-5 py-2.5 rounded-xl font-bold hover:bg-rose-100 uppercase text-[10px] tracking-widest transition-all"
          >
            Löschen
          </button>
        </div>
      </div>

      {/* SELL FORM */}
      {showSellForm && (
        <div className="mb-8 bg-amber-50 border border-amber-100 p-8 rounded-[2rem] animate-in slide-in-from-top duration-300 shadow-xl">
          <form onSubmit={handleSell} className="flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-amber-800 text-[10px] font-black uppercase mb-2 ml-1 tracking-widest">Menge</label>
                <input 
                  type="number" step="any" value={sellQuantity} 
                  onChange={(e) => setSellQuantity(e.target.value)} 
                  placeholder={`MAX: ${qty.toFixed(2)}`} 
                  className="w-full bg-white border-none rounded-2xl py-4 px-4 focus:ring-2 focus:ring-amber-500 font-bold shadow-inner" required 
                />
              </div>
              <div className="relative">
                <label className="block text-amber-800 text-[10px] font-black uppercase mb-2 ml-1 tracking-widest">
                  Verkaufspreis (in {portfolioCurrency})
                </label>
                <input 
                  type="number" step="any" value={sellPrice} 
                  onChange={(e) => setSellPrice(e.target.value)} 
                  placeholder="Marktwert nutzen" 
                  className="w-full bg-white border-none rounded-2xl py-4 px-4 focus:ring-2 focus:ring-amber-500 font-bold shadow-inner" 
                />
                <div className="absolute right-4 bottom-4 text-amber-600 font-black text-xs opacity-40">{portfolioCurrency}</div>
              </div>
            </div>
            <button type="submit" disabled={isActionLoading} className="w-full bg-amber-500 text-white py-5 rounded-2xl font-black uppercase text-xs tracking-widest hover:bg-amber-600 active:scale-95 transition-all shadow-lg shadow-amber-200">
              {isActionLoading ? "Verbuche..." : "Verkauf bestätigen"}
            </button>
          </form>
        </div>
      )}

      {/* MAIN CONTENT CARD */}
      <div className="bg-white rounded-[2.5rem] p-10 shadow-xl border border-slate-100 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-32 -mt-32 opacity-30"></div>
        
        <div className="relative z-10">
          <span className="text-indigo-600 font-black uppercase tracking-[0.2em] text-[10px] bg-indigo-50 px-3 py-1 rounded-full">Asset Details</span>
          <h2 className="text-4xl font-black text-slate-900 mt-4 tracking-tighter">{item.asset?.name}</h2>
          <p className="text-slate-400 font-bold text-lg mb-8 tracking-widest">{item.asset?.symbol} | {item.asset?.isin}</p>

          <div className="grid grid-cols-2 gap-8 border-t border-slate-50 pt-8">
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase mb-1 tracking-widest">Aktueller Bestand</p>
              <p className="text-3xl font-black text-slate-800 tabular-nums">{qty.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-slate-400 text-[10px] font-black uppercase mb-1 tracking-widest">Ø Einstiegspreis</p>
              <p className="text-3xl font-black text-slate-800 tabular-nums">
                {formatCurrency(avgPrice, portfolioCurrency)}
              </p>
            </div>
          </div>

          <div className="mt-10 p-8 bg-slate-900 rounded-[2rem] text-white shadow-2xl relative overflow-hidden group">
            <div className="absolute inset-0 bg-indigo-500 opacity-0 group-hover:opacity-5 transition-opacity"></div>
            <p className="opacity-60 text-[10px] font-black uppercase tracking-[0.3em]">Investiertes Kapital (Einstiegswert)</p>
            <p className="text-5xl font-black mt-3 tabular-nums text-indigo-400 tracking-tighter">
              {formatCurrency(qty * avgPrice, portfolioCurrency)}
            </p>
          </div>
        </div>
      </div>

      {/* DELETE MODAL */}
      {showDeleteConfirm && (
        <DeleteConfirmModal 
          title={`${item.asset?.name} (${item.asset?.symbol})`}
          isLoading={isActionLoading}
          onClose={() => setShowDeleteConfirm(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}