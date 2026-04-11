import React, { useState } from 'react';

export default function Register({ onSwitchToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 1. E-Mail Validierung
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        setError('Bitte gib eine gültige E-Mail-Adresse an (z.B. name@beispiel.de).');
        return; 
    }

    // 2. Passwort Validierung
    if (password.length < 6) {
        setError('Das Passwort ist zu kurz. Es muss mindestens 6 Zeichen lang sein.');
        return;
    }

    setIsLoading(true);

    try {
      // NUTZT JETZT DIE IP AUS DER DOCKER-COMPOSE
      // Wichtig: /auth/register wird an http://192.168.178.42:8000/api/v1 angehängt
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registrierung fehlgeschlagen.');
      }

      setSuccess(true);
      setTimeout(() => onSwitchToLogin(), 2000);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center border border-emerald-100">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Konto erstellt!</h2>
          <p className="text-slate-500 mt-2">Du wirst nun zum Login weitergeleitet...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-slate-900">Konto erstellen</h2>
          <p className="text-slate-500 mt-2">Starte jetzt mit deinem Portfolio-Tracker</p>
        </div>

        {error && (
          <div className="bg-rose-50 text-rose-600 p-4 rounded-xl mb-6 text-sm font-semibold border border-rose-100 animate-pulse">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Benutzername</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all" 
              placeholder="Dein Wunschname" 
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">E-Mail</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all" 
              placeholder="deine@mail.de" 
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Passwort</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-500 outline-none transition-all" 
              placeholder="Mind. 6 Zeichen" 
              required 
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className={`w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-xl shadow-lg transition-all ${isLoading ? 'opacity-50' : ''}`}
          >
            {isLoading ? 'Wird registriert...' : 'Registrieren'}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-8">
          Bereits ein Konto?{" "}
          <button 
            type="button" 
            onClick={onSwitchToLogin} 
            className="text-indigo-600 font-bold hover:underline"
          >
            Einloggen
          </button>
        </p>
      </div>
    </div>
  );
}