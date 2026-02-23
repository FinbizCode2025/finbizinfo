import React, { useEffect, useState } from 'react';
import { useAuth } from './auth';

export default function Profile() {
  const { token, logout } = useAuth();
  const [user, setUser] = useState<{ username: string; email?: string } | null>(null);
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({ username: '', email: '' });
  const [message, setMessage] = useState('');

  // Fetch user details from backend
  useEffect(() => {
    async function fetchProfile() {
      const res = await fetch('http://127.0.0.1:5002/api/profile', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        setForm({ username: data.username, email: data.email || '' });
      }
    }
    fetchProfile();
  }, [token]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    const res = await fetch('http://127.0.0.1:5002/api/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    });
    if (res.ok) {
      setMessage('Profile updated successfully!');
      setEdit(false);
      setUser({ ...user!, ...form });
    } else {
      setMessage('Failed to update profile.');
    }
  };

  if (!user) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded shadow text-center">
        Loading profile...
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded shadow">
      <h2 className="mb-4 text-lg font-bold text-center">Profile</h2>
      {edit ? (
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block mb-1 font-medium">Username</label>
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div>
            <label className="block mb-1 font-medium">Email</label>
            <input
              name="email"
              value={form.email}
              onChange={handleChange}
              className="w-full p-2 border rounded"
              type="email"
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
              Save
            </button>
            <button
              type="button"
              className="bg-gray-400 text-white px-4 py-2 rounded"
              onClick={() => setEdit(false)}
            >
              Cancel
            </button>
          </div>
          {message && <div className="text-green-600">{message}</div>}
        </form>
      ) : (
        <div>
          <div className="mb-2">
            <strong>Username:</strong> {user.username}
          </div>
          <div className="mb-2">
            <strong>Email:</strong> {user.email || <span className="text-gray-400">Not set</span>}
          </div>
          <div className="flex gap-2 mt-4">
            <button
              className="bg-blue-500 text-white px-4 py-2 rounded"
              onClick={() => setEdit(true)}
            >
              Edit Profile
            </button>
            <button
              className="bg-red-500 text-white px-4 py-2 rounded"
              onClick={logout}
            >
              Logout
            </button>
          </div>
          {message && <div className="text-green-600 mt-2">{message}</div>}
        </div>
      )}
    </div>
  );
}