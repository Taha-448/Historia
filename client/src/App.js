import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import PatientPortal from './PatientPortal';
import DoctorDashboard from './DoctorDashboard';
import './App.css';

function App() {
  const [messages, setMessages] = React.useState([{ sender: 'AI', text: 'Hello, I am Historia, your medical assistant. How can I help you today?' }]);
  const [input, setInput] = React.useState('');

  return (
    <Router>
      <div className="App">
        {/* Navigation Navbar */}
        <nav className="navbar">
          <div className="navbar-brand">Historia - A History Taking Nurse</div>
          <div className="navbar-links">
            <Link to="/" className="nav-link">Patient Portal</Link>
            <Link to="/doctor" className="nav-link">Doctor Dashboard</Link>
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
            <Route path="/doctor" element={<DoctorDashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;