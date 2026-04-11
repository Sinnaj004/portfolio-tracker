import React, { useState, useEffect } from 'react';

export default function Navbar({ onLogout }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setUser(data);
        }
      } catch (err) {
        console.error("Fehler beim Laden des Profils", err);
      }
    };
    fetchUser();
  }, []);

  return (
    <nav className="bg-white sticky top-0 z-[100] border-b-2 border-slate-900">
      <div className="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
        
        {/* Branding - Minimalistisch */}
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-8 h-8 bg-slate-900 rounded flex items-center justify-center text-white transition-transform group-hover:rotate-6">
            <span className="font-black text-lg">P</span>
          </div>
          <span className="font-black text-slate-900 tracking-tighter text-xl uppercase italic">
            Vault
          </span>
        </div>

        {/* User Bereich - Die "Schwarze Linie" Optik */}
        <div className="flex items-center gap-6">
          {user ? (
            <div className="flex items-center gap-4">
              {/* User Info */}
              <div className="flex flex-col items-end">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">
                  Verified User
                </span>
                <span className="text-sm font-black text-slate-900">
                  {user.username}
                </span>
              </div>

              {/* Vertikaler Trenner (Der schwarze Strich Effekt) */}
              <div className="h-8 w-[2px] bg-slate-900/10"></div>

              {/* Logout Button */}
              <button 
                onClick={onLogout}
                className="group flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg text-xs font-black hover:bg-indigo-600 transition-all active:scale-95 shadow-lg shadow-slate-200"
              >
                <span>LOGOUT</span>
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  width="14" 
                  height="14" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="3" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  className="group-hover:translate-x-0.5 transition-transform"
                >
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
              </button>
            </div>
          ) : (
            <div className="h-8 w-32 bg-slate-100 animate-pulse rounded"></div>
          )}
        </div>
      </div>
    </nav>
  );
}