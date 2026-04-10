import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [view, setView] = useState('login'); // 'login' oder 'register'

  // Beim Laden prüfen, ob ein Token existiert
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setView('login');
  };

  // 1. Wenn eingeloggt -> Dashboard zeigen
  if (isAuthenticated) {
    return <Dashboard onLogout={handleLogout} />;
  }

  // 2. Wenn nicht eingeloggt -> Zwischen Login und Register wählen
  return (
    <div className="w-full min-h-screen bg-slate-50">
      {view === 'login' ? (
        <Login 
          onLoginSuccess={() => setIsAuthenticated(true)} 
          onSwitchToRegister={() => setView('register')} 
        />
      ) : (
        <Register 
          onSwitchToLogin={() => setView('login')} 
        />
      )}
    </div>
  );
}

export default App;