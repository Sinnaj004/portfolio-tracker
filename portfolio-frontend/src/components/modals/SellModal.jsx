import React, { useState } from 'react';

export default function SellModal({ asset, onClose, onConfirm }) {
  const [amount, setAmount] = useState("");

  if (!asset) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
        <h3 className="text-xl font-bold mb-2">Bestand verkaufen</h3>
        <p className="text-slate-500 mb-6">
          Anteile von <span className="font-bold text-slate-800">{asset.symbol}</span> verkaufen.
          <br/>
          <span className="text-xs text-indigo-600">Verfügbar: {asset.quantity}</span>
        </p>
        
        <input 
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full border-2 border-slate-100 rounded-xl px-4 py-3 mb-6 focus:border-indigo-500 outline-none transition-all"
          placeholder="Menge..."
        />

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 px-4 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl">
            Abbrechen
          </button>
          <button 
            onClick={() => onConfirm(asset, amount)}
            className="flex-1 px-4 py-3 bg-rose-500 text-white font-bold rounded-xl hover:bg-rose-600"
          >
            Verkaufen
          </button>
        </div>
      </div>
    </div>
  );
}