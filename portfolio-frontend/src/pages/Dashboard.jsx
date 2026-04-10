import React, { useState } from 'react';
import StatCard from '../components/dashboard/StatCard';
import SellModal from '../components/modals/SellModal';
import { formatCurrency, calculateGrowth } from '../utils/formatters';

// Platzhalter-Daten (werden später durch API-Calls ersetzt)
const MOCK_DATA = [
  { id: 1, name: "Apple Inc.", symbol: "AAPL", quantity: 15, avgPrice: 175.50, currentPrice: 182.30 },
  { id: 2, name: "Microsoft", symbol: "MSFT", quantity: 8, avgPrice: 310.20, currentPrice: 405.15 },
  { id: 3, name: "Bitcoin", symbol: "BTC", quantity: 0.05, avgPrice: 42000.00, currentPrice: 63500.00 },
];

export default function Dashboard({ onLogout }) {
  const [selectedAsset, setSelectedAsset] = useState(null);

  const handleSellConfirm = (asset, amount) => {
    console.log(`Verkaufs-Anfrage: ${amount} Stück von ${asset.symbol}`);
    // Hier kommt später der DELETE oder POST Request ans Backend
    setSelectedAsset(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Header / Nav */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-indigo-600 tracking-tight">PortfolioVault</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500 hidden sm:inline">Eingeloggt als User</span>
            <button 
              onClick={onLogout}
              className="bg-slate-100 hover:bg-rose-50 hover:text-rose-600 text-slate-700 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
            >
              Abmelden
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-10">
        {/* Statistik-Karten */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <StatCard title="Gesamtwert" value={12450.45} />
          <StatCard title="Tagesänderung" value="+2,4%" isCurrency={false} trend={true} />
          <StatCard title="Anzahl Assets" value={MOCK_DATA.length} isCurrency={false} />
        </div>

        {/* Portfolio Tabelle */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h2 className="text-lg font-bold text-slate-800">Deine Bestände</h2>
            <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-md">
              + Asset hinzufügen
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Asset</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Menge</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Kaufpreis</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Gesamtwert</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Aktionen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {MOCK_DATA.map((item) => {
                  const growth = calculateGrowth(item.avgPrice, item.currentPrice);
                  return (
                    <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-slate-900">{item.symbol}</div>
                        <div className="text-sm text-slate-500">{item.name}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-medium text-slate-700">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-600">
                        {formatCurrency(item.avgPrice)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="font-bold text-indigo-600">
                          {formatCurrency(item.quantity * item.currentPrice)}
                        </div>
                        <div className={`text-xs font-bold ${growth.isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
                          {growth.isPositive ? '▲' : '▼'} {growth.value}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => setSelectedAsset(item)}
                          className="text-slate-400 hover:text-rose-500 font-medium transition-colors"
                        >
                          Verkaufen
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Das Modal wird nur angezeigt, wenn ein Asset ausgewählt wurde */}
      {selectedAsset && (
        <SellModal 
          asset={selectedAsset} 
          onClose={() => setSelectedAsset(null)} 
          onConfirm={handleSellConfirm}
        />
      )}
    </div>
  );
}