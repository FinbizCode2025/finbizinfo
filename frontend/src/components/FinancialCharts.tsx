import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts';

interface FinancialChartsProps {
  markdown: string;
}

const COLORS = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7'];

const FinancialCharts: React.FC<FinancialChartsProps> = ({ markdown }) => {
  const [ratios, setRatios] = useState<{ [key: string]: { [year: string]: number } }>({});
  const [expenses, setExpenses] = useState<{ [year: string]: { [category: string]: number } }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!markdown || !markdown.trim()) {
      setRatios({});
      setExpenses({});
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    fetch('https://finbizinfo.com/api/api/ai-ratios-graph', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to generate charts');
        setRatios(data.ratios || {});
        setExpenses(data.expenses || {});
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [markdown]);

  const ratioNames = Object.keys(ratios);

  // Combined expenses for all years (for overall pie chart)
  const combinedExpenses: { [category: string]: number } = {};
  Object.values(expenses).forEach(yearObj => {
    Object.entries(yearObj).forEach(([cat, value]) => {
      combinedExpenses[cat] = (combinedExpenses[cat] || 0) + value;
    });
  });
  const combinedExpenseData = Object.entries(combinedExpenses).map(([name, value]) => ({ name, value }));

  // Pie chart for each year
  const expenseYears = Object.keys(expenses);

  if (!markdown || !markdown.trim()) return null;

  return (
    <div style={{ marginTop: 32 }}>
      <h3 style={{ fontWeight: 600, fontSize: '1.2rem' }}>Financial Ratios (Bar Charts)</h3>
      {loading && <div>Generating charts...</div>}
      {error && <div style={{ color: 'red' }}>{error}</div>}

      {/* Bar charts for ratios */}
      {ratioNames.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 32 }}>
          {ratioNames.map((ratio, idx) => {
            const yearsObj = ratios[ratio];
            const data = Object.entries(yearsObj).map(([year, value]) => ({
              year,
              value,
            }));
            if (data.length < 2) return null;
            return (
              <div key={ratio} style={{ minWidth: 260, flex: '1 1 260px', textAlign: 'center' }}>
                <h4>{ratio}</h4>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="value"
                      fill={COLORS[idx % COLORS.length]}
                      name={ratio}
                      barSize={30}
                    />
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 8 }}>
                  <strong>Values:</strong>{' '}
                  {data.map((d) => `${d.year}: ${d.value}`).join(', ')}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pie chart for all expenses (all years combined) */}
      {combinedExpenseData.length > 0 && (
        <div style={{ marginTop: 40, textAlign: 'center' }}>
          <h3 style={{ fontWeight: 600, fontSize: '1.1rem' }}>All Expenses (All Years)</h3>
          <ResponsiveContainer width={320} height={320}>
            <PieChart>
              <Pie
                data={combinedExpenseData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={120}
                fill="#8884d8"
                label
              >
                {combinedExpenseData.map((entry, i) => (
                  <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Pie chart for each year's expenses */}
      {expenseYears.length > 0 && (
        <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap', marginTop: 40 }}>
          {expenseYears.map((year, idx) => {
            const data = Object.entries(expenses[year]).map(([cat, value]) => ({
              name: cat,
              value,
            }));
            if (data.length === 0) return null;
            return (
              <div key={year} style={{ minWidth: 220, textAlign: 'center' }}>
                <h4>Expenses {year}</h4>
                <ResponsiveContainer width={220} height={220}>
                  <PieChart>
                    <Pie
                      data={data}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      label
                    >
                      {data.map((entry, i) => (
                        <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FinancialCharts;