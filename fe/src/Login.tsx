import React, { useState } from 'react';
import { useAuth } from './auth';
import { useNavigate, Link } from 'react-router-dom';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('http://127.0.0.1:5002/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok && data.access_token) {
        login(data.access_token);
        navigate('/');
      } else {
        setError(data.error || 'Invalid credentials');
      }
    } catch (err) {
      setError('Unable to connect to server.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-xs mx-auto mt-20 p-6 bg-white rounded shadow">
      <h2 className="mb-4 text-lg font-bold">Login</h2>
      <input
        className="block w-full mb-2 p-2 border"
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        required
      />
      <input
        className="block w-full mb-2 p-2 border"
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      {error && <div className="text-red-500 mb-2">{error}</div>}
      <button className="w-full bg-blue-500 text-white py-2 rounded" type="submit">Login</button>
      <div className="mt-4 text-center">
        <span>Don't have an account? </span>
        <Link to="/register" className="text-blue-600 underline">Register</Link>
      </div>
    </form>
  );
}