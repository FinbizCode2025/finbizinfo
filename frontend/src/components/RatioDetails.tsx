import React from 'react';

interface RatioData {
  [key: string]: number;
}

interface RatioInfo {
  name: string;
  value: number;
  formula: string;
  interpretation: string;
  healthIndicator: 'good' | 'warning' | 'poor';
  benchmark?: string;
  calculation?: string;
}

const RatioDetails: React.FC<{ ratios: RatioData; balanceSheetData?: any }> = ({ ratios }) => {
  // Define ratio information with formulas and interpretations
  const ratioDefinitions: { [key: string]: Omit<RatioInfo, 'value'> } = {
    current_ratio: {
      name: 'Current Ratio',
      formula: 'Current Assets ÷ Current Liabilities',
      interpretation: 'Measures the company\'s ability to pay short-term obligations. A ratio of 1.5-3.0 is generally considered healthy.',
      healthIndicator: 'good',
      benchmark: '1.5 - 3.0',
      calculation: 'Shows how many dollars of current assets the company has for every dollar of current liabilities.',
    },
    quick_ratio: {
      name: 'Quick Ratio',
      formula: '(Current Assets - Inventory) ÷ Current Liabilities',
      interpretation: 'More conservative than current ratio, excludes inventory. A ratio above 1.0 is generally good.',
      healthIndicator: 'good',
      benchmark: '> 1.0',
      calculation: 'Measures immediate liquidity without relying on inventory sales.',
    },
    cash_ratio: {
      name: 'Cash Ratio',
      formula: 'Cash & Equivalents ÷ Current Liabilities',
      interpretation: 'Most conservative liquidity measure. Shows what percentage of current liabilities can be paid immediately.',
      healthIndicator: 'good',
      benchmark: '0.5 - 1.0',
      calculation: 'Indicates immediate debt repayment capability.',
    },
    gross_margin: {
      name: 'Gross Margin',
      formula: '(Revenue - COGS) ÷ Revenue × 100%',
      interpretation: 'Percentage of revenue remaining after paying cost of goods sold. Higher is better.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (20-50%)',
      calculation: 'Measures production efficiency and pricing power.',
    },
    operating_margin: {
      name: 'Operating Margin',
      formula: 'Operating Income ÷ Revenue × 100%',
      interpretation: 'Percentage of revenue left after paying operating expenses. Shows operational efficiency.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (5-20%)',
      calculation: 'Reflects how well the company manages its core business operations.',
    },
    net_margin: {
      name: 'Net Profit Margin',
      formula: 'Net Income ÷ Revenue × 100%',
      interpretation: 'Percentage of revenue that becomes profit. Considers all expenses including taxes and interest.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (3-10%)',
      calculation: 'Overall profitability after all expenses.',
    },
    roa: {
      name: 'Return on Assets (ROA)',
      formula: 'Net Income ÷ Total Assets × 100%',
      interpretation: 'How efficiently the company uses its assets to generate profit. Higher is better.',
      healthIndicator: 'good',
      benchmark: '> 5%',
      calculation: 'Measures asset productivity and management efficiency.',
    },
    roe: {
      name: 'Return on Equity (ROE)',
      formula: 'Net Income ÷ Shareholders\' Equity × 100%',
      interpretation: 'Return generated on shareholders\' investment. Higher indicates better returns to investors.',
      healthIndicator: 'good',
      benchmark: '> 10-15%',
      calculation: 'Shows how effectively equity capital generates profits.',
    },
    debt_ratio: {
      name: 'Debt Ratio',
      formula: 'Total Debt ÷ Total Assets × 100%',
      interpretation: 'Percentage of assets financed by debt. Lower is generally better.',
      healthIndicator: 'good',
      benchmark: '< 50%',
      calculation: 'Indicates financial leverage and risk level.',
    },
    debt_to_equity: {
      name: 'Debt-to-Equity Ratio',
      formula: 'Total Debt ÷ Shareholders\' Equity',
      interpretation: 'Compares debt to equity financing. Lower means less risky.',
      healthIndicator: 'good',
      benchmark: '< 1.0',
      calculation: 'Shows the balance between debt and equity financing.',
    },
    equity_multiplier: {
      name: 'Equity Multiplier',
      formula: 'Total Assets ÷ Shareholders\' Equity',
      interpretation: 'Measures financial leverage. Shows how much assets are financed by equity.',
      healthIndicator: 'good',
      benchmark: '1.5 - 2.5',
      calculation: 'Indicates the extent of financial leverage.',
    },
    interest_coverage: {
      name: 'Interest Coverage Ratio',
      formula: 'EBIT ÷ Interest Expense',
      interpretation: 'How many times the company can cover interest payments with earnings. Higher is safer.',
      healthIndicator: 'good',
      benchmark: '> 2.5',
      calculation: 'Shows ability to service debt obligations.',
    },
    asset_turnover: {
      name: 'Asset Turnover Ratio',
      formula: 'Revenue ÷ Total Assets',
      interpretation: 'How efficiently assets generate revenue. Higher means better asset utilization.',
      healthIndicator: 'good',
      benchmark: '> 1.0',
      calculation: 'Measures how productively assets are used.',
    },
    inventory_turnover: {
      name: 'Inventory Turnover Ratio',
      formula: 'COGS ÷ Average Inventory',
      interpretation: 'How many times inventory is sold and replaced. Higher indicates efficient inventory management.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (3-8)',
      calculation: 'Shows how quickly inventory is converted to sales.',
    },
    receivables_turnover: {
      name: 'Receivables Turnover Ratio',
      formula: 'Revenue ÷ Average Accounts Receivable',
      interpretation: 'How efficiently the company collects receivables. Higher is better.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (4-10)',
      calculation: 'Indicates effectiveness of credit and collection policies.',
    },
    payables_turnover: {
      name: 'Payables Turnover Ratio',
      formula: 'COGS ÷ Average Accounts Payable',
      interpretation: 'How quickly the company pays suppliers. Balance between cash flow management and relationships.',
      healthIndicator: 'good',
      benchmark: 'Varies by industry (4-8)',
      calculation: 'Shows payment efficiency and supplier relationship management.',
    },
  };

  const getHealthColor = (indicator: string): string => {
    switch (indicator) {
      case 'good':
        return 'border-l-4 border-green-500 bg-green-50';
      case 'warning':
        return 'border-l-4 border-yellow-500 bg-yellow-50';
      case 'poor':
        return 'border-l-4 border-red-500 bg-red-50';
      default:
        return 'border-l-4 border-blue-500 bg-blue-50';
    }
  };

  const getHealthBadge = (indicator: string): React.ReactNode => {
    switch (indicator) {
      case 'good':
        return <span className="inline-block px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm font-semibold">✓ Healthy</span>;
      case 'warning':
        return <span className="inline-block px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-semibold">⚠ Warning</span>;
      case 'poor':
        return <span className="inline-block px-3 py-1 bg-red-200 text-red-800 rounded-full text-sm font-semibold">✗ Poor</span>;
      default:
        return <span className="inline-block px-3 py-1 bg-blue-200 text-blue-800 rounded-full text-sm font-semibold">ℹ Info</span>;
    }
  };

  if (!ratios || Object.keys(ratios).length === 0) {
    return (
      <div className="p-6 bg-gray-100 rounded-lg text-center">
        <p className="text-gray-600">No ratio data available. Please upload a financial document.</p>
      </div>
    );
  }

  // Group ratios by category
  const ratiosByCategory = {
    'Liquidity Analysis': {
      icon: '💧',
      description: 'Measures the company\'s ability to meet short-term obligations',
      ratios: ['current_ratio', 'quick_ratio', 'cash_ratio'],
    },
    'Profitability Analysis': {
      icon: '📈',
      description: 'Measures how effectively the company generates profit',
      ratios: ['gross_margin', 'operating_margin', 'net_margin', 'roa', 'roe'],
    },
    'Leverage Analysis': {
      icon: '⚖️',
      description: 'Measures the extent of debt financing and financial risk',
      ratios: ['debt_ratio', 'debt_to_equity', 'equity_multiplier', 'interest_coverage'],
    },
    'Efficiency Analysis': {
      icon: '⚡',
      description: 'Measures how well the company uses its assets',
      ratios: ['asset_turnover', 'inventory_turnover', 'receivables_turnover', 'payables_turnover'],
    },
  };

  return (
    <div className="space-y-8 w-full">
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-8 rounded-lg shadow-lg">
        <h1 className="text-4xl font-bold mb-2">📊 Comprehensive Financial Ratio Analysis</h1>
        <p className="text-blue-100">Detailed breakdown of all financial ratios with formulas, calculations, and interpretations</p>
      </div>

      {Object.entries(ratiosByCategory).map(([categoryName, categoryData]) => (
        <div key={categoryName} className="space-y-4">
          <div className="flex items-center space-x-3 border-b-2 border-gray-300 pb-4">
            <span className="text-4xl">{categoryData.icon}</span>
            <div>
              <h2 className="text-3xl font-bold text-gray-800">{categoryName}</h2>
              <p className="text-gray-600">{categoryData.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {categoryData.ratios.map((ratioKey) => {
              const definition = ratioDefinitions[ratioKey];
              const value = ratios[ratioKey];

              if (!definition) return null;

              return (
                <div key={ratioKey} className={`p-6 rounded-lg shadow-md ${getHealthColor(definition.healthIndicator)} space-y-3`}>
                  {/* Header */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">{definition.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{definition.calculation}</p>
                    </div>
                    {getHealthBadge(definition.healthIndicator)}
                  </div>

                  {/* Value */}
                  <div className="bg-white p-4 rounded border-2 border-gray-300">
                    <p className="text-gray-600 text-sm font-semibold">Calculated Value:</p>
                    <p className="text-3xl font-bold text-blue-600">
                      {typeof value === 'number' ? (
                        value > 1 ? value.toFixed(2) : (value * 100).toFixed(2) + '%'
                      ) : (
                        'N/A'
                      )}
                    </p>
                  </div>

                  {/* Formula */}
                  <div className="bg-white p-4 rounded border-l-4 border-blue-500">
                    <p className="text-gray-600 text-sm font-semibold mb-2">📐 Formula:</p>
                    <p className="font-mono text-sm text-gray-800 bg-gray-100 p-3 rounded">
                      {definition.formula}
                    </p>
                  </div>

                  {/* Benchmark */}
                  {definition.benchmark && (
                    <div className="bg-white p-4 rounded border-l-4 border-green-500">
                      <p className="text-gray-600 text-sm font-semibold mb-1">🎯 Healthy Benchmark:</p>
                      <p className="text-gray-800 font-semibold">{definition.benchmark}</p>
                    </div>
                  )}

                  {/* Interpretation */}
                  <div className="bg-white p-4 rounded border-l-4 border-purple-500">
                    <p className="text-gray-600 text-sm font-semibold mb-2">💡 What It Means:</p>
                    <p className="text-gray-800 text-sm leading-relaxed">{definition.interpretation}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <hr className="my-8" />
        </div>
      ))}

      {/* Summary Section */}
      <div className="bg-gradient-to-r from-purple-100 to-pink-100 p-8 rounded-lg border-2 border-purple-300">
        <h3 className="text-2xl font-bold text-gray-800 mb-4">📋 Key Takeaways</h3>
        <ul className="space-y-3 text-gray-700">
          <li className="flex items-start">
            <span className="text-2xl mr-3">✓</span>
            <div>
              <p className="font-semibold">Liquidity Position:</p>
              <p className="text-sm">How quickly the company can convert assets to cash and pay obligations</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="text-2xl mr-3">✓</span>
            <div>
              <p className="font-semibold">Profitability Strength:</p>
              <p className="text-sm">The company's ability to generate profits at various levels (gross, operating, net)</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="text-2xl mr-3">✓</span>
            <div>
              <p className="font-semibold">Financial Risk:</p>
              <p className="text-sm">The extent to which the company relies on debt vs equity financing</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="text-2xl mr-3">✓</span>
            <div>
              <p className="font-semibold">Operational Efficiency:</p>
              <p className="text-sm">How effectively the company utilizes its assets to generate revenue</p>
            </div>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default RatioDetails;
