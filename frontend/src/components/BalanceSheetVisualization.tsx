import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface BalanceSheetVisualizationProps {
  comprehensiveBS?: any;
}

const COLORS = ['#667eea', '#764ba2', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#42a5f5', '#ab47bc'];

const BalanceSheetVisualization: React.FC<BalanceSheetVisualizationProps> = ({ comprehensiveBS }) => {
  if (!comprehensiveBS) return null;

  const assets = comprehensiveBS.assets || {};
  const liabilitiesAndEquity = comprehensiveBS.liabilities_and_equity || {};

  // Prepare data for asset composition pie chart
  const assetCompositionData = [
    {
      name: 'Current Assets',
      value: assets.current_assets?.total || 0,
      category: 'current'
    },
    {
      name: 'Non-Current Assets',
      value: assets.non_current_assets?.total || 0,
      category: 'non-current'
    }
  ].filter(item => item.value > 0);

  // Prepare data for liability & equity pie chart
  const liabilityEquityData = [
    {
      name: 'Current Liabilities',
      value: liabilitiesAndEquity.current_liabilities?.total || 0,
      category: 'current'
    },
    {
      name: 'Non-Current Liabilities',
      value: liabilitiesAndEquity.non_current_liabilities?.total || 0,
      category: 'non-current'
    },
    {
      name: 'Shareholders\' Equity',
      value: liabilitiesAndEquity.equity?.total || 0,
      category: 'equity'
    }
  ].filter(item => item.value > 0);

  // Prepare data for balance sheet bar chart
  const balanceSheetData = [
    {
      name: 'Current Assets',
      value: assets.current_assets?.total || 0
    },
    {
      name: 'Non-Current Assets',
      value: assets.non_current_assets?.total || 0
    },
    {
      name: 'Current Liabilities',
      value: liabilitiesAndEquity.current_liabilities?.total || 0
    },
    {
      name: 'Non-Current Liabilities',
      value: liabilitiesAndEquity.non_current_liabilities?.total || 0
    },
    {
      name: 'Shareholders\' Equity',
      value: liabilitiesAndEquity.equity?.total || 0
    }
  ].filter(item => item.value > 0);

  // Prepare data for detailed asset breakdown
  const detailedAssetData = [
    ...Object.entries(assets.current_assets?.items || {}).map(([name, value]: any) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat(value) || 0,
      type: 'Current Asset'
    })),
    ...Object.entries(assets.non_current_assets?.items || {}).map(([name, value]: any) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat(value) || 0,
      type: 'Non-Current Asset'
    }))
  ].filter(item => item.value > 0).slice(0, 10); // Top 10 items

  // Prepare data for detailed liability breakdown
  const detailedLiabilityData = [
    ...Object.entries(liabilitiesAndEquity.current_liabilities?.items || {}).map(([name, value]: any) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat(value) || 0,
      type: 'Current Liability'
    })),
    ...Object.entries(liabilitiesAndEquity.non_current_liabilities?.items || {}).map(([name, value]: any) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat(value) || 0,
      type: 'Non-Current Liability'
    })),
    ...Object.entries(liabilitiesAndEquity.equity?.items || {}).map(([name, value]: any) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat(value) || 0,
      type: 'Equity'
    }))
  ].filter(item => item.value > 0).slice(0, 10); // Top 10 items

  // Calculate totals for summary
  const totalAssets = assets.total_assets || 0;
  const totalLiabilities = liabilitiesAndEquity.total_liabilities || 0;
  const totalEquity = liabilitiesAndEquity.equity?.total || 0;

  const formatValue = (value: number) => {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)}Cr`;
    } else if (value >= 100000) {
      return `₹${(value / 100000).toFixed(2)}L`;
    } else {
      return `₹${(value / 1000).toFixed(0)}K`;
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          padding: '10px',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
        }}>
          <p style={{ margin: '0', fontSize: '12px', fontWeight: '600' }}>{payload[0].name}</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', fontWeight: '700', color: payload[0].fill }}>
            {formatValue(payload[0].value)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ marginTop: '30px', padding: '20px', background: '#f8f9fc', borderRadius: '12px' }}>
      <h3 style={{
        fontSize: '22px',
        fontWeight: '700',
        color: '#2c3e50',
        marginBottom: '30px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        📊 Balance Sheet Visualization
      </h3>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'white',
          padding: '16px',
          borderRadius: '8px',
          border: '2px solid #667eea',
          boxShadow: '0 2px 8px rgba(102, 126, 234, 0.1)'
        }}>
          <p style={{ margin: '0', fontSize: '12px', color: '#666', fontWeight: '600' }}>Total Assets</p>
          <p style={{ margin: '8px 0 0 0', fontSize: '20px', fontWeight: '700', color: '#667eea' }}>
            {formatValue(totalAssets)}
          </p>
        </div>
        <div style={{
          background: 'white',
          padding: '16px',
          borderRadius: '8px',
          border: '2px solid #e15759',
          boxShadow: '0 2px 8px rgba(225, 87, 89, 0.1)'
        }}>
          <p style={{ margin: '0', fontSize: '12px', color: '#666', fontWeight: '600' }}>Total Liabilities</p>
          <p style={{ margin: '8px 0 0 0', fontSize: '20px', fontWeight: '700', color: '#e15759' }}>
            {formatValue(totalLiabilities)}
          </p>
        </div>
        <div style={{
          background: 'white',
          padding: '16px',
          borderRadius: '8px',
          border: '2px solid #59a14f',
          boxShadow: '0 2px 8px rgba(89, 161, 79, 0.1)'
        }}>
          <p style={{ margin: '0', fontSize: '12px', color: '#666', fontWeight: '600' }}>Shareholders\' Equity</p>
          <p style={{ margin: '8px 0 0 0', fontSize: '20px', fontWeight: '700', color: '#59a14f' }}>
            {formatValue(totalEquity)}
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
        gap: '24px',
        marginBottom: '30px'
      }}>
        {/* Asset Composition Pie Chart */}
        {assetCompositionData.length > 0 && (
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)'
          }}>
            <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
              💰 Asset Composition
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={assetCompositionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {assetCompositionData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Liability & Equity Composition Pie Chart */}
        {liabilityEquityData.length > 0 && (
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)'
          }}>
            <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
              🏦 Liabilities & Equity Composition
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={liabilityEquityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {liabilityEquityData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[(index + 3) % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Balance Sheet Components Bar Chart */}
      {balanceSheetData.length > 0 && (
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
          marginBottom: '24px'
        }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
            📊 Balance Sheet Components Comparison
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={balanceSheetData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" fill="#667eea" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Detailed Asset Breakdown */}
      {detailedAssetData.length > 0 && (
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
          marginBottom: '24px'
        }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
            🏢 Detailed Asset Breakdown (Top 10)
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={detailedAssetData} layout="vertical" margin={{ top: 5, right: 30, left: 300, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={290} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" fill="#667eea" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Detailed Liability & Equity Breakdown */}
      {detailedLiabilityData.length > 0 && (
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)'
        }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
            🔗 Detailed Liabilities & Equity Breakdown (Top 10)
          </h4>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={detailedLiabilityData} layout="vertical" margin={{ top: 5, right: 30, left: 300, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={290} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" fill="#764ba2" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default BalanceSheetVisualization;
