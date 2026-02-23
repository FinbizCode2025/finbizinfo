import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts';

interface FinancialChartsProps {
  sessionId: string;
}

const COLORS = ['#667eea', '#764ba2', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1'];

const FinancialCharts: React.FC<FinancialChartsProps> = ({ sessionId }) => {
  const [assetComposition, setAssetComposition] = useState<Array<{ name: string; value: number }>>([]);
  const [liabilityComposition, setLiabilityComposition] = useState<Array<{ name: string; value: number }>>([]);
  const [ratios, setRatios] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateCharts = () => {
    if (!sessionId) return;
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('session_id', sessionId);
    fetch('http://127.0.0.1:5002/api/ai-ratios-graph', {
      method: 'POST',
      body: formData,
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to generate charts');
        
        // Convert asset composition object to array
        const assets = Object.entries(data.asset_composition || {}).map(([name, value]: any) => ({
          name,
          value: parseFloat(value) || 0
        }));
        
        // Convert liability composition object to array
        const liabilities = Object.entries(data.liability_composition || {}).map(([name, value]: any) => ({
          name,
          value: parseFloat(value) || 0
        }));
        
        // Convert ratios object to array
        const ratioArray = Object.entries(data.ratios || {}).map(([name, yearData]: any) => ({
          name,
          value: parseFloat(yearData['Current Year']) || 0
        }));
        
        setAssetComposition(assets);
        setLiabilityComposition(liabilities);
        setRatios(ratioArray);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  if (!sessionId) return null;

  return (
    <div style={{ marginTop: 40, padding: '20px', background: '#f8f9fc', borderRadius: '12px' }}>
      <h2 style={{ 
        fontWeight: 700, 
        fontSize: '24px',
        color: '#2c3e50',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        📊 Financial Visualizations
      </h2>
      
      <button
        onClick={handleGenerateCharts}
        disabled={loading}
        style={{
          marginBottom: 24,
          padding: '12px 28px',
          fontWeight: 600,
          fontSize: 16,
          cursor: loading ? 'not-allowed' : 'pointer',
          background: loading ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          boxShadow: loading ? 'none' : '0 4px 15px rgba(102, 126, 234, 0.4)',
          transition: 'all 0.3s ease',
          opacity: loading ? 0.7 : 1
        }}
        onMouseEnter={(e) => {
          if (!loading) {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
          }
        }}
        onMouseLeave={(e) => {
          if (!loading) {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
          }
        }}
      >
        {loading ? '⏳ Generating...' : '📈 Generate Charts'}
      </button>
      
      {error && <div style={{ color: '#e74c3c', marginBottom: '20px', padding: '12px', background: '#fadbd8', borderRadius: '6px', fontWeight: '600' }}>❌ {error}</div>}

      {/* Asset Composition Pie Chart */}
      {assetComposition.length > 0 && (
        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          marginBottom: '32px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
        }}>
          <h3 style={{ 
            fontWeight: 600, 
            fontSize: '18px',
            color: '#667eea',
            marginBottom: '20px'
          }}>💰 Asset Composition</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={assetComposition}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ₹${(value / 100000).toFixed(0)}L`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {assetComposition.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => `₹${(value / 100000).toFixed(2)}L`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Liability Composition Pie Chart */}
      {liabilityComposition.length > 0 && (
        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          marginBottom: '32px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
        }}>
          <h3 style={{ 
            fontWeight: 600, 
            fontSize: '18px',
            color: '#764ba2',
            marginBottom: '20px'
          }}>📊 Liability Composition</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={liabilityComposition}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ₹${(value / 100000).toFixed(0)}L`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {liabilityComposition.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => `₹${(value / 100000).toFixed(2)}L`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Key Ratios Bar Chart */}
      {ratios.length > 0 && (
        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          marginBottom: '32px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
        }}>
          <h3 style={{ 
            fontWeight: 600, 
            fontSize: '18px',
            color: '#f28e2b',
            marginBottom: '20px'
          }}>📈 Key Financial Metrics</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart
              data={ratios}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={120}
                tick={{ fontSize: 12 }}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: any) => {
                  // Format based on metric type
                  if (typeof value === 'number' && value < 10) {
                    return value.toFixed(2); // Likely a ratio
                  }
                  return `₹${(value / 100000).toFixed(2)}L`;
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar dataKey="value" fill="#667eea" name="Value" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {assetComposition.length === 0 && liabilityComposition.length === 0 && ratios.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          background: 'white',
          borderRadius: '12px',
          color: '#7f8c8d',
          fontSize: '16px'
        }}>
          <p>📋 Click "Generate Charts" to visualize financial data</p>
        </div>
      )}
    </div>
  );
};

export default FinancialCharts;
