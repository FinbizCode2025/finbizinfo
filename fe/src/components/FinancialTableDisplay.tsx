import React, { useState } from 'react';
import './FinancialTableDisplay.css';

interface RatioData {
  [key: string]: {
    [key: string]: number | undefined;
  } | number | undefined;
}

interface FinancialTableDisplayProps {
  ratios: RatioData | { ratios: RatioData; _extracted_numbers?: { [key: string]: number | undefined } };
  extractedNumbers?: {
    [key: string]: number | undefined;
  };
}

const FinancialTableDisplay: React.FC<FinancialTableDisplayProps> = ({ ratios, extractedNumbers }) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['current_ratio', 'quick_ratio', 'liquidity_ratios']));

  // Handle both flat and nested ratio structures
  const getRatiosData = () => {
    if (!ratios) return {};
    
    // If ratios has a 'ratios' key, it's the new structured format
    if (ratios.ratios && typeof ratios.ratios === 'object' && !Array.isArray(ratios.ratios)) {
      return ratios.ratios;
    }
    
    // Otherwise it's flat, organize into categories
    const organized: { [key: string]: { [key: string]: number | undefined } } = {
      liquidity_ratios: {},
      profitability_ratios: {},
      solvency_ratios: {},
      efficiency_ratios: {},
      activity_ratios: {},
      working_capital_ratios: {},
      dupont_analysis: {},
    };
    
    const liquidityKeys = ['current_ratio', 'quick_ratio', 'cash_ratio', 'working_capital', 'working_capital_ratio'];
    const profitabilityKeys = ['gross_margin', 'gross_profit', 'operating_margin', 'operating_profit', 'net_margin', 'net_profit', 'roa', 'roe', 'ebitda_margin', 'ebit_margin', 'return_on_sales'];
    const solvencyKeys = ['debt_to_equity', 'debt_ratio', 'equity_ratio', 'interest_coverage', 'debt_service_coverage', 'leverage_ratio', 'long_term_debt_to_equity', 'assets_to_liabilities'];
    const efficiencyKeys = ['asset_turnover', 'current_assets_ratio', 'fixed_assets_ratio', 'receivables_to_current_assets', 'asset_base'];
    const activityKeys = ['fixed_asset_turnover', 'current_asset_turnover', 'receivables_turnover', 'days_sales_outstanding', 'inventory_turnover', 'receivables_turnover'];
    const workingCapitalKeys = ['operating_cash_ratio'];
    const dupontKeys = ['net_profit_margin', 'equity_multiplier', 'roe_dupont'];

    Object.entries(ratios).forEach(([key, value]) => {
      if (key === '_extracted_numbers' || key === 'ratios') return;
      
      if (typeof value === 'number') {
        if (liquidityKeys.includes(key)) organized.liquidity_ratios[key] = value;
        else if (profitabilityKeys.includes(key)) organized.profitability_ratios[key] = value;
        else if (solvencyKeys.includes(key)) organized.solvency_ratios[key] = value;
        else if (efficiencyKeys.includes(key)) organized.efficiency_ratios[key] = value;
        else if (activityKeys.includes(key)) organized.activity_ratios[key] = value;
        else if (workingCapitalKeys.includes(key)) organized.working_capital_ratios[key] = value;
        else if (dupontKeys.includes(key)) organized.dupont_analysis[key] = value;
      }
    });
    
    return organized;
  };

  const ratiosData = getRatiosData();
  
  // Get extracted numbers
  const getExtractedNumbers = () => {
    if (extractedNumbers) return extractedNumbers;
    if (ratios && ratios._extracted_numbers) return ratios._extracted_numbers;
    return {};
  };

  const extracted = getExtractedNumbers();

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const formatValue = (value: number | undefined, key: string): string => {
    if (value === undefined || value === null) return 'N/A';

    // Percentages
    if (key.includes('margin') || key.includes('ratio_percent') || key.includes('quality')) {
      return `${(value * 100).toFixed(2)}%`;
    }

    // Ratios (smaller decimal)
    if (key.includes('ratio') || key.includes('turnover') || key.includes('coverage')) {
      return value.toFixed(4);
    }

    // Currency values
    if (key.includes('assets') || key.includes('liability') || key.includes('equity') || 
        key.includes('income') || key.includes('profit') || key.includes('capital')) {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }

    return value.toFixed(2);
  };

  const getStatusBadge = (key: string, value: number | undefined): React.ReactNode => {
    if (value === undefined || value === null) return null;

    let status = '';
    let color = '';

    // Liquidity metrics
    if (key === 'current_ratio') {
      if (value >= 1.5 && value <= 3.0) {
        status = '✓ Good';
        color = 'green';
      } else if (value < 1.0) {
        status = '⚠ Warning';
        color = 'red';
      } else {
        status = '→ Review';
        color = 'orange';
      }
    } else if (key === 'quick_ratio') {
      if (value >= 1.0) {
        status = '✓ Good';
        color = 'green';
      } else {
        status = '⚠ Warning';
        color = 'red';
      }
    }

    // Leverage metrics
    else if (key === 'debt_to_equity') {
      if (value <= 1.5) {
        status = '✓ Good';
        color = 'green';
      } else {
        status = '⚠ High';
        color = 'red';
      }
    } else if (key === 'debt_ratio') {
      if (value <= 0.4) {
        status = '✓ Good';
        color = 'green';
      } else if (value <= 0.6) {
        status = '→ Moderate';
        color = 'orange';
      } else {
        status = '⚠ High';
        color = 'red';
      }
    }

    // Profitability metrics
    else if (key === 'net_margin' || key === 'roa' || key === 'roe') {
      if (value >= 0.15) {
        status = '✓ Good';
        color = 'green';
      } else if (value >= 0.05) {
        status = '→ Monitor';
        color = 'orange';
      } else {
        status = '⚠ Weak';
        color = 'red';
      }
    }

    if (status) {
      return (
        <span className={`status-badge status-${color}`}>
          {status}
        </span>
      );
    }

    return null;
  };

  const categoryLabels: { [key: string]: { label: string; icon: string; description: string } } = {
    liquidity_ratios: {
      label: 'Liquidity Ratios',
      icon: '💧',
      description: 'Measures the company\'s ability to meet short-term obligations',
    },
    solvency_ratios: {
      label: 'Solvency & Leverage Ratios',
      icon: '🏦',
      description: 'Measures the company\'s long-term financial stability and debt capacity',
    },
    profitability_ratios: {
      label: 'Profitability Ratios',
      icon: '📈',
      description: 'Measures how effectively the company generates profit',
    },
    activity_ratios: {
      label: 'Activity & Turnover Ratios',
      icon: '🔄',
      description: 'Measures how efficiently the company uses assets to generate revenue',
    },
    efficiency_ratios: {
      label: 'Efficiency Ratios',
      icon: '⚙️',
      description: 'Measures asset utilization effectiveness',
    },
    working_capital_ratios: {
      label: 'Working Capital Ratios',
      icon: '💼',
      description: 'Measures operational efficiency and cash management',
    },
    dupont_analysis: {
      label: 'DuPont Analysis',
      icon: '🔍',
      description: 'Breaks ROE into profitability, efficiency, and leverage components',
    },
  };

  const formatKey = (key: string): string => {
    return key
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const renderCategoryTable = (category: string, data: { [key: string]: number | undefined }) => {
    const categoryInfo = categoryLabels[category];
    if (!categoryInfo) return null;

    const isExpanded = expandedCategories.has(category);
    const entries = Object.entries(data).filter(([_, value]) => value !== undefined && value !== null);

    if (entries.length === 0) return null;

    return (
      <div key={category} className="ratio-category">
        <div className="category-header" onClick={() => toggleCategory(category)}>
          <div className="header-content">
            <span className="category-icon">{categoryInfo.icon}</span>
            <div className="header-text">
              <h3 className="category-title">{categoryInfo.label}</h3>
              <p className="category-description">{categoryInfo.description}</p>
            </div>
          </div>
          <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
        </div>

        {isExpanded && (
          <div className="category-content">
            <table className="financial-table">
              <thead>
                <tr>
                  <th className="metric-column">Metric</th>
                  <th className="value-column">Value</th>
                  <th className="status-column">Status</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(([key, value]) => (
                  <tr key={key}>
                    <td className="metric-column">
                      <span className="metric-name">{formatKey(key)}</span>
                    </td>
                    <td className="value-column">
                      <span className="metric-value">{formatValue(value, key)}</span>
                    </td>
                    <td className="status-column">
                      {getStatusBadge(key, value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="financial-table-display">
      <div className="table-header">
        <h2>📊 Financial Ratios Analysis</h2>
        <p className="subtitle">Comprehensive financial metrics organized by category</p>
      </div>

      <div className="ratios-container">
        {Object.entries(ratiosData).map(([category, data]) => {
          if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
            return renderCategoryTable(category, data as { [key: string]: number | undefined });
          }
          return null;
        })}
      </div>

      {extracted && Object.keys(extracted).length > 0 && (
        <div className="extracted-data-section">
          <div className="section-header">
            <h3>📋 Base Financial Data</h3>
            <p className="section-description">Extracted from the financial document</p>
          </div>
          <table className="financial-table data-table">
            <thead>
              <tr>
                <th className="metric-column">Item</th>
                <th className="value-column">Amount</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(extracted || {})
                .filter(([_, value]) => value !== undefined && value !== null)
                .map(([key, value]) => (
                  <tr key={key}>
                    <td className="metric-column">
                      <span className="metric-name">{formatKey(key)}</span>
                    </td>
                    <td className="value-column">
                      <span className="metric-value">{formatValue(value, key)}</span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FinancialTableDisplay;
