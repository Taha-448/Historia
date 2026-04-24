import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import PatientPortal from './PatientPortal';
import DoctorDashboard from './DoctorDashboard';
import Login from './Login';
import './App.css';

function App() {
  const [messages, setMessages] = useState([{ sender: 'AI', text: 'Hello, I am Historia, your medical assistant. How can I help you today?' }]);
  const [input, setInput] = useState('');
  
  // Auth State
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('staffUser')) || null);

  const handleLogin = (userData) => {
    localStorage.setItem('staffUser', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('staffUser');
    setUser(null);
  };

  return (
    <Router>
      <div className="App">
        {/* Navigation Navbar */}
        <nav className="navbar">
          <div className="navbar-brand">Historia - Medical Triage System</div>
          <div className="navbar-links">
            <Link to="/" className="nav-link">Patient Portal</Link>
            {!user ? (
               <Link to="/login" className="nav-link">Staff Login</Link>
            ) : (
                <>
                    <span className="user-badge">👤 {user.username} ({user.role})</span>
                    <Link to="/doctor" className="nav-link">Dashboard</Link>
                    <span onClick={handleLogout} className="nav-link logout-link">Logout</span>
                </>
            )}
          </div>
        </nav>

        {/* Route Selector */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={
              <PatientPortal 
                messages={messages} 
                setMessages={setMessages} 
                input={input} 
                setInput={setInput} 
              />
            } />
            <Route path="/login" element={
                user ? <Navigate to="/doctor" /> : <Login onLogin={handleLogin} />
            } />
            <Route path="/doctor" element={
                user ? <DoctorDashboard user={user} /> : <Navigate to="/login" />
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;