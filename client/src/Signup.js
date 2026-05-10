import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('doctor');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('role', role);

      const response = await axios.post('http://localhost:8000/signup', formData);
      setMessage(response.data.detail);
      
      // Clear form on success
      setUsername('');
      setPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account. Username might be taken.');
    }
  };

  return (
    <div className="container login-container">
      <div className="login-box">
        <h2>📝 Staff Registration</h2>
        <p>Create a new account for the Historia Medical Portal.</p>
        
        {message && <div className="success-alert" style={{ backgroundColor: '#d4edda', color: '#155724', padding: '10px', borderRadius: '5px', marginBottom: '15px' }}>{message}</div>}
        {error && <div className="error-alert" style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '10px', borderRadius: '5px', marginBottom: '15px' }}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              placeholder="Pick a username"
              required 
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••"
              required 
            />
          </div>

          <div className="form-group">
            <label>Role</label>
            <select 
                value={role} 
                onChange={(e) => setRole(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
                <option value="doctor">Doctor (Requires Admin Approval)</option>
                <option value="nurse">Nurse</option>
                <option value="admin">Admin</option>
            </select>
          </div>
          
          <button type="submit" className="login-btn">Register Account</button>
        </form>
        
        <div className="login-footer">
          Already have an account? <Link to="/login">Sign In here</Link>
        </div>
      </div>
    </div>
  );
}

export default Signup;
