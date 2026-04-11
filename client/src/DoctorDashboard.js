import React, { useState, useEffect } from 'react';
import axios from 'axios';

function DoctorDashboard() {
  const [activePatients, setActivePatients] = useState([]);
  const [summary, setSummary] = useState('');

  const fetchActivePatients = async () => {
    try {
      const response = await axios.get('http://localhost:8000/active_sessions');
      setActivePatients(response.data.sessions);
    } catch(error) {
      console.error("Failed to fetch patients:", error);
    }
  };

  useEffect(() => {
    fetchActivePatients();
    const interval = setInterval(() => {
        fetchActivePatients();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const generateSummary = async (sessionId) => {
    try {
      setSummary("Generating summary for Session #" + sessionId + "...");
      const response = await axios.get(`http://127.0.0.1:8000/summary?session_id=${sessionId}`);
      setSummary(response.data.summary);
      fetchActivePatients();
    } catch (error) {
      console.error("Error generating summary", error);
      setSummary("Failed to generate summary. Please check Rate Limits or Server Logs.");
    }
  };

  return (
    <div className="container dashboard">
      <div className="dashboard-content">
        <h2 style={{ color: '#d9534f' }}>🩺 Live Doctor Dashboard</h2>
        <button onClick={fetchActivePatients} className="refresh-btn">
          ↻ Refresh Waiting Room
        </button>
        
        <h4>Patients waiting for Triage Review:</h4>
        {activePatients.length === 0 ? (
          <p><i>No active patients in the queue right now.</i></p>
        ) : (
          <ul className="patient-list">
            {activePatients.map(patient => (
              <li key={patient.session_id} className="patient-card">
                <strong>Session ID:</strong> #{patient.session_id} <br/>
                <strong>Phone Source:</strong> {patient.phone_number} <br/>
                <strong>Started At:</strong> {new Date(patient.created_at).toLocaleTimeString()} <br/>
                <button 
                  onClick={() => generateSummary(patient.session_id)} 
                  className="summary-btn"
                >
                  Generate Medical Summary
                </button>
              </li>
            ))}
          </ul>
        )}
        
        {summary && (
          <div className="report-panel">
            <strong>Final Medical Report:</strong><br/><br/>
            {summary}
          </div>
        )}
      </div>
    </div>
  );
}

export default DoctorDashboard;
