import React, { useState } from 'react';
import axios from 'axios';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // Use form data as required by FastAPI OAuth2
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('http://localhost:8000/login', formData);
      
      const { access_token, role } = response.data;
      onLogin({ username, role, token: access_token });
    } catch (err) {
      // Display the specific error message from the backend (e.g. "Account pending verification")
      setError(err.response?.data?.detail || 'Invalid username or password');
    }
  };

  return (
    <div className="container login-container">
      <div className="login-box">
        <h2>🏥 Medical Staff Login</h2>
        <p>Please enter your credentials to access the portal.</p>
        
        {error && <div className="error-alert" style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '10px', borderRadius: '5px', marginBottom: '15px' }}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          {/* ... existing input fields ... */}
          <div className="form-group">
            <label>Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              placeholder="e.g. taha"
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
          
          <button type="submit" className="login-btn">Sign In to Dashboard</button>
        </form>
        
        <div className="login-footer">
          <p>New staff member? <a href="/signup">Create an account</a></p>
          <small>Restricted Access - Authorized Personnel Only</small>
        </div>
      </div>
    </div>
  );
}

export default Login;
