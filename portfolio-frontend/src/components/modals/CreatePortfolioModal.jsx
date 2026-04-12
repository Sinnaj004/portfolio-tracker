import React, { useState } from 'react';

export default function CreatePortfolioModal({ onClose, onRefresh }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [currency, setCurrency] = useState('EUR'); // Standard auf EUR
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Liste der verfügbaren Währungen
  const currencies = [
    { code: 'EUR', label: 'Euro (€)', symbol: '€' },
    { code: 'USD', label: 'US Dollar ($)', symbol: '$' },
    { code: 'CHF', label: 'Schweizer Franken (CHF)', symbol: 'Fr.' },
    { code: 'GBP', label: 'Britisches Pfund (£)', symbol: '£' },
    { code: 'JPY', label: 'Japanischer Yen (¥)', symbol: '¥' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/portfolio/`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        // Currency wird jetzt mitgeschickt
        body: JSON.stringify({ name, description, currency }) 
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Fehler beim Erstellen");
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
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-xl font-bold text-slate-800">Neues Portfolio</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-rose-50 text-rose-600 p-3 rounded-lg text-sm font-medium border border-rose-100">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Name</label>
            <input 
              type="text" 
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all"
              placeholder="z.B. Dividenden Strategie"
            />
          </div>

          {/* NEU: WÄHRUNGS-AUSWAHL */}
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Portfolio-Währung</label>
            <div className="relative">
              <select 
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all bg-white appearance-none cursor-pointer font-medium"
              >
                {currencies.map(curr => (
                  <option key={curr.code} value={curr.code}>
                    {curr.label}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 mt-1 ml-1 uppercase font-bold tracking-wider">
              Basis für alle Berechnungen in diesem Depot
            </p>
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Beschreibung</label>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all h-20 resize-none"
              placeholder="Wofür ist dieses Portfolio gedacht?"
            />
          </div>

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
              className="flex-1 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-100 transition-all disabled:opacity-50"
            >
              {isLoading ? "Speichere..." : "Erstellen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}