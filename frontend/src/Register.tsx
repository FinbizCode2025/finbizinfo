import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      const res = await fetch('https://finbizinfo.com/api/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, email }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess('Registration successful! You can now log in.');
        setTimeout(() => navigate('/login'), 1500);
      } else {
        setError(data.error || 'Registration failed');
      }
    } catch (err) {
      setError('Unable to connect to server.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-xs mx-auto mt-20 p-6 bg-white rounded shadow">
      <h2 className="mb-4 text-lg font-bold">Register</h2>
      <input
        className="block w-full mb-2 p-2 border"
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        required
      />
      <input
        className="block w-full mb-2 p-2 border"
        type="email"
        placeholder="Email (optional)"
        value={email}
        onChange={e => setEmail(e.target.value)}
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
      {success && <div className="text-green-600 mb-2">{success}</div>}
      <button className="w-full bg-blue-500 text-white py-2 rounded" type="submit">Register</button>
      <div className="mt-4 text-center">
        <span>Already have an account? </span>
        <Link to="/login" className="text-blue-600 underline">Login</Link>
      </div>
    </form>
  );
}