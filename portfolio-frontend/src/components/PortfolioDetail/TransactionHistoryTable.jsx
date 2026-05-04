import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../../utils/formatters';

export default function TransactionHistoryTable({ portfolioId, portfolioCurrency }) {
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      const token = localStorage.getItem('token');

      try {
        setIsLoading(true);
        setError(null);
        
        // Einfacher GET-Request ohne Limit/Offset Parameter
        const res = await fetch(`/api/v1/portfolio/${portfolioId}/transactions`, {
          headers: { 
            "Authorization": `Bearer ${token}`, 
            "Content-Type": "application/json" 
          }
        });

        if (!res.ok) throw new Error("Fehler beim Laden der Transaktionshistorie");
        
        const data = await res.json();
        setTransactions(data);
      } catch (err) {
        console.error("Fetch Error:", err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (portfolioId) {
      fetchTransactions();
    }
  }, [portfolioId]);

  const getTransactionBadge = (type) => {
    const isBuy = type.toUpperCase() === 'BUY';
    return (
      <span className={`px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${
        isBuy ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
      }`}>
        {type}
      </span>
    );
  };

  if (isLoading) {
    return <div className="p-20 text-center animate-pulse text-slate-400 font-bold uppercase tracking-widest text-xs">Lade Historie...</div>;
  }

  if (error) {
    return <div className="p-20 text-center text-rose-500 font-bold text-sm">⚠️ {error}</div>;
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 text-[10px] uppercase font-black tracking-wider">
            <tr>
              <th className="px-6 py-4">Datum</th>
              <th className="px-4 py-4 text-center">Typ</th>
              <th className="px-4 py-4">Asset</th>
              <th className="px-4 py-4 text-right">Menge</th>
              <th className="px-4 py-4 text-right">Kurs (Asset)</th>
              <th className="px-4 py-4 text-right">Gesamt ({portfolioCurrency})</th>
              <th className="px-6 py-4 text-right">Real. G/V</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan="7" className="py-20 text-center text-slate-400 text-sm font-medium">
                  Keine Transaktionen in diesem Portfolio gefunden.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4 text-xs font-medium text-slate-500 whitespace-nowrap">
                    {new Date(tx.transaction_date).toLocaleDateString('de-DE', { 
                        day: '2-digit', month: 'short', year: 'numeric' 
                    })}
                  </td>
                  <td className="px-4 py-4 text-center">
                    {getTransactionBadge(tx.type)}
                  </td>
                  <td className="px-4 py-4">
                    <div className="font-bold text-slate-900 text-sm">{tx.asset_symbol}</div>
                    <div className="text-[10px] text-slate-400 font-bold truncate max-w-[120px]">
                      {tx.asset_name}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right tabular-nums text-sm font-medium">
                    {parseFloat(tx.quantity).toLocaleString()}
                  </td>
                  <td className="px-4 py-4 text-right tabular-nums text-xs text-slate-500">
                    {parseFloat(tx.price_per_unit).toFixed(2)} {portfolioCurrency}
                  </td>
                  <td className="px-4 py-4 text-right tabular-nums font-bold text-slate-900">
                    {formatCurrency(tx.total_amount, portfolioCurrency)}
                  </td>
                  <td className={`px-6 py-4 text-right tabular-nums font-black text-sm ${
                    parseFloat(tx.realized_pnl) >= 0 ? 'text-emerald-500' : 'text-rose-500'
                  }`}>
                    {tx.realized_pnl ? (
                      <>
                        {parseFloat(tx.realized_pnl) > 0 ? '+' : ''}
                        {formatCurrency(tx.realized_pnl, portfolioCurrency)}
                      </>
                    ) : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}