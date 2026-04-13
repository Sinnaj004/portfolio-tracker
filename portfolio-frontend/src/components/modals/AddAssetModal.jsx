import React, { useState } from 'react';

// 1. portfolioCurrency oben in den Props aufnehmen
export default function AddAssetModal({ portfolioId, portfolioCurrency, onClose, onRefresh }) {
  const [symbol, setSymbol] = useState('');
  const [isin, setIsin] = useState('');
  const [quantity, setQuantity] = useState('');
  const [avgCostPrice, setAvgCostPrice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!symbol && !isin) {
      setError('Bitte gib entweder ein Symbol (Ticker) oder eine ISIN an.');
      return;
    }

    setIsLoading(true);
    const token = localStorage.getItem('token');

    const payload = {
      quantity: parseFloat(quantity) || 0,
      avg_cost_price: parseFloat(avgCostPrice) || 0,
      symbol: symbol || null,
      isin: isin || null
    };

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio_item/${portfolioId}/items`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Asset konnte nicht gefunden oder hinzugefügt werden.");
      }

      onRefresh();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      {/* CSS um Pfeile in den Zahlenfeldern zu entfernen */}
      <style>{`
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        input[type=number] { -moz-appearance: textfield; appearance: textfield; }
      `}</style>

      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-xl font-bold text-slate-800">Asset hinzufügen</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-rose-50 text-rose-600 p-3 rounded-lg text-sm font-medium border border-rose-100">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Ticker / Symbol</label>
              <input 
                type="text" 
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all uppercase"
                placeholder="z.B. AAPL"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">ISIN</label>
              <input 
                type="text" 
                value={isin}
                onChange={(e) => setIsin(e.target.value.toUpperCase())}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all uppercase"
                placeholder="US0378331005"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Menge</label>
              <input 
                type="number" 
                step="any"
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all"
                placeholder="1.0"
              />
            </div>
            <div>
              {/* HIER: Dynamische Währung im Label anzeigen */}
              <label className="block text-sm font-bold text-slate-700 mb-1">Kaufpreis ({portfolioCurrency})</label>
              <input 
                type="number" 
                step="any"
                required
                value={avgCostPrice}
                onChange={(e) => setAvgCostPrice(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all"
                placeholder="150.00"
              />
            </div>
          </div>

          <p className="text-[11px] text-slate-400 italic">
            * Das System sucht automatisch nach aktuellen Kursen basierend auf Ticker oder ISIN.
          </p>

          <div className="flex gap-3 pt-4">
            <button 
              type="button" 
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 font-bold hover:bg-slate-50 transition-all"
            >
              Abbrechen
            </button>
            <button 
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-lg transition-all disabled:opacity-50"
            >
              {isLoading ? "Suche läuft..." : "Hinzufügen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}