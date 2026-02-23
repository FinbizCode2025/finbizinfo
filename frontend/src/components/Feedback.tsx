import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth';

const Feedback: React.FC = () => {
  const { setUser } = useAuth();
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  // Fetch user credentials from /api/profile endpoint using JWT token
  useEffect(() => {
    const fetchProfile = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch('http://127.0.0.1:5002/api/profile', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setUserEmail(data.email);
          if (setUser) setUser({ email: data.email });
        }
      } catch (err) {
        // Optionally handle error
      }
      setLoading(false);
    };
    fetchProfile();
  }, [setUser]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!feedback.trim()) {
      setError('Please enter your feedback.');
      return;
    }
    try {
      const res = await fetch('http://127.0.0.1:5002/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: userEmail, feedback }),
      });
      if (!res.ok) throw new Error('Failed to submit feedback');
      setSubmitted(true);
      setFeedback('');
    } catch (err) {
      setError('Could not submit feedback. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-700"></div>
        <span className="ml-4 text-blue-700 font-semibold">Loading...</span>
      </div>
    );
  }

  if (!userEmail) {
    return (
      <div className="p-8 bg-white rounded-xl shadow-lg text-gray-700 max-w-lg mx-auto mt-16 border border-gray-200">
        <div className="flex flex-col items-center">
          <svg className="w-12 h-12 text-blue-400 mb-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16 17l-4 4m0 0l-4-4m4 4V3" />
          </svg>
          <p className="text-lg font-medium">Please log in to submit feedback.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto mt-16 p-8 bg-white rounded-2xl shadow-xl border border-gray-200">
      <div className="flex items-center mb-6">
        <div className="bg-blue-100 rounded-full p-3 mr-4">
          <svg className="w-7 h-7 text-blue-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8s-9-3.582-9-8a9 9 0 1118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-bold text-blue-800">We Value Your Feedback</h2>
          <p className="text-gray-500 text-sm">Help us improve your experience</p>
        </div>
      </div>
      {submitted ? (
        <div className="flex flex-col items-center py-12">
          <svg className="w-16 h-16 text-green-500 mb-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <div className="text-green-700 text-lg font-semibold mb-2">Thank you for your feedback!</div>
          <div className="text-gray-500">We appreciate your input and will use it to improve our services.</div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 font-semibold mb-1">Your Email</label>
            <input
              type="email"
              value={userEmail || ''}
              disabled
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-gray-700 font-semibold mb-1">Your Feedback</label>
            <textarea
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              rows={5}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-200 focus:outline-none resize-none"
              placeholder="Share your thoughts, suggestions, or report an issue..."
              required
            />
          </div>
          {error && <div className="text-red-600 text-sm">{error}</div>}
          <div className="flex justify-end">
            <button
              type="submit"
              className="bg-blue-700 hover:bg-blue-800 text-white font-semibold px-6 py-2 rounded-lg shadow transition"
            >
              Submit Feedback
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default Feedback;