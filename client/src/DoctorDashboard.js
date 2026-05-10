import React, { useState, useEffect } from 'react';
import axios from 'axios';

function DoctorDashboard({ user }) {
  const [activePatients, setActivePatients] = useState([]);
  const [summary, setSummary] = useState('');
  const [view, setView] = useState('waiting'); // 'waiting', 'analytics', 'audit', or 'staff'
  const [analytics, setAnalytics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [pendingStaff, setPendingStaff] = useState([]);

  console.log("Current View:", view);

  const fetchActivePatients = async () => {
    try {
      const response = await axios.get('http://localhost:8000/active_sessions', {
          headers: { Authorization: `Bearer ${user.token}` }
      });
      setActivePatients(response.data.sessions);
    } catch(error) {
      console.error("Failed to fetch patients:", error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/analytics', {
          headers: { Authorization: `Bearer ${user.token}` }
      });
      setAnalytics(response.data);
    } catch(error) {
      console.error("Failed to fetch analytics:", error);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await axios.get('http://localhost:8000/audit_logs', {
          headers: { Authorization: `Bearer ${user.token}` }
      });
      setLogs(response.data.logs);
    } catch(error) {
      console.error("Failed to fetch logs:", error);
    }
  };
  const fetchPendingStaff = async () => {
    try {
      const response = await axios.get('http://localhost:8000/admin/pending_staff', {
          headers: { Authorization: `Bearer ${user.token}` }
      });
      console.log("API Response for Pending Staff:", response.data);
      setPendingStaff(response.data.pending || []);
    } catch(error) {
      console.error("Failed to fetch pending staff:", error);
    }
  };

  const handleVerifyStaff = async (username) => {
    try {
        await axios.post(`http://localhost:8000/admin/verify_staff?username=${username}`, {}, {
            headers: { Authorization: `Bearer ${user.token}` }
        });
        fetchPendingStaff(); // Refresh the list
        alert(`User ${username} verified successfully!`);
    } catch (error) {
        alert("Failed to verify user.");
    }
  };

  useEffect(() => {
    if (view === 'waiting') {
        fetchActivePatients();
        const interval = setInterval(fetchActivePatients, 10000);
        return () => clearInterval(interval);
    } else if (view === 'analytics') {
        fetchAnalytics();
    } else if (view === 'audit') {
        fetchLogs();
    } else if (view === 'staff') {
        fetchPendingStaff();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const generateSummary = async (sessionId) => {
    try {
      setSummary("Generating summary for Session #" + sessionId + "...");
      const response = await axios.get(`http://localhost:8000/summary?session_id=${sessionId}`, {
          headers: { Authorization: `Bearer ${user.token}` }
      });
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
        <h2 style={{ color: '#2c3e50' }}>🩺 Doctor Portal</h2>
        
        <div className="tab-navigation">
          <button 
            className={`tab-btn ${view === 'waiting' ? 'active' : ''}`}
            onClick={() => setView('waiting')}
          >
            Live Waiting Room
          </button>
          
          {['doctor', 'admin'].includes(user.role) && (
            <>
              <button 
                className={`tab-btn ${view === 'analytics' ? 'active' : ''}`}
                onClick={() => setView('analytics')}
              >
                Practice Analytics
              </button>
              <button 
                className={`tab-btn ${view === 'audit' ? 'active' : ''}`}
                onClick={() => setView('audit')}
              >
                System Audit Logs
              </button>
              {user.role === 'admin' && (
                <button 
                  className={`tab-btn ${view === 'staff' ? 'active' : ''}`}
                  onClick={() => setView('staff')}
                >
                  Manage Staff
                </button>
              )}
            </>
          )}
        </div>

        {view === 'waiting' ? (
          <>
            <button onClick={fetchActivePatients} className="refresh-btn">
              ↻ Refresh Waiting Room
            </button>
            
            <h4>Patients waiting for Triage Review:</h4>
            {activePatients.length === 0 ? (
              <p><i>No active patients in the queue right now.</i></p>
            ) : (
              <ul className="patient-list">
                {activePatients.map(patient => (
                  <li 
                    key={patient.session_id} 
                    className={`patient-card ${patient.is_critical ? 'critical' : ''}`}
                  >
                    <strong>Session ID:</strong> #{patient.session_id} 
                    {patient.is_critical && <span className="critical-badge">🚨 Critical Alert</span>}
                    <br/>
                    <strong>Phone Source:</strong> {patient.phone_number} <br/>
                    <strong>Started At:</strong> {new Date(patient.created_at).toLocaleTimeString()} <br/>
                    {['doctor', 'admin'].includes(user.role) ? (
                        <button 
                        onClick={() => generateSummary(patient.session_id)} 
                        className="summary-btn"
                        >
                        {patient.is_active ? "Generate Medical Summary" : "View Critical Report"}
                        </button>
                    ) : (
                        <button className="summary-btn disabled" disabled>
                            {patient.is_active ? "Awaiting Doctor Review" : "Report Generated"}
                        </button>
                    )}
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
          </>
        ) : view === 'analytics' ? (
          <div className="analytics-view">
            <h3>Weekly Practice Insights</h3>
            {analytics ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-value">{analytics.stats?.avg_triage_minutes?.toFixed(1) || 0}m</span>
                  <span className="stat-label">Avg. Triage Time</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{analytics.stats?.total_sessions || 0}</span>
                  <span className="stat-label">Weekly Patients</span>
                </div>
                <div className="stat-card" style={{ borderColor: '#d9534f' }}>
                  <span className="stat-value" style={{ color: '#d9534f' }}>{analytics.stats?.critical_count || 0}</span>
                  <span className="stat-label">Critical Cases</span>
                </div>

                <div className="symptom-chart-container">
                  <h4>Common Symptom Frequency</h4>
                  {analytics.symptoms?.map(s => (
                    <div key={s.symptom} className="symptom-row">
                      <div className="symptom-name">{s.symptom}</div>
                      <div className="symptom-bar-bg">
                        <div 
                          className="symptom-bar" 
                          style={{ width: `${(s.occurrence_count / (analytics.stats?.total_sessions || 1)) * 100}%` }}
                        ></div>
                      </div>
                      <div className="symptom-count">{s.occurrence_count}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p>Loading analytics...</p>
            )}
          </div>
        ) : view === 'audit' ? (
          <div className="audit-view">
            <h3>Recent System Activity</h3>
            <div className="table-responsive">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>ID</th>
                    <th>Summary Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.log_id}>
                      <td className="time-col">{new Date(log.performed_at).toLocaleString()}</td>
                      <td><span className={`action-badge ${log.action_type.toLowerCase()}`}>{log.action_type}</span></td>
                      <td>#{log.record_id}</td>
                      <td className="log-msg-col">
                        {log.action_type === 'INSERT' ? (
                           <div className="log-new">{log.new_value}</div>
                        ) : (
                          <div className="log-diff">
                            <del>{log.old_value}</del> <span className="arrow">→</span> <ins>{log.new_value}</ins>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : view === 'staff' ? (
          <div className="staff-view">
            <h3>Pending Staff Verification</h3>
            <p>The following users have signed up and are awaiting approval.</p>
            {pendingStaff.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', border: '1px dashed #ccc', borderRadius: '8px', marginTop: '20px' }}>
                    <p><i>No pending verifications found in the database.</i></p>
                </div>
            ) : (
                <div className="table-responsive">
                    <table className="audit-table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Role</th>
                                <th>Requested At</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pendingStaff.map(staff => (
                                <tr key={staff.username}>
                                    <td>{staff.username}</td>
                                    <td><strong>{staff.role.charAt(0).toUpperCase() + staff.role.slice(1)}</strong></td>
                                    <td>{new Date(staff.created_at).toLocaleDateString()}</td>
                                    <td>
                                        <button 
                                            onClick={() => handleVerifyStaff(staff.username)}
                                            className="summary-btn"
                                            style={{ backgroundColor: '#28a745', fontSize: '12px', padding: '5px 10px', width: 'auto' }}
                                        >
                                            Approve & Verify
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
          </div>
        ) : (
            <div style={{ padding: '20px', textAlign: 'center' }}>
                <p>Please select a tab above to view data.</p>
            </div>
        )}
      </div>
    </div>
  );
}

export default DoctorDashboard;
