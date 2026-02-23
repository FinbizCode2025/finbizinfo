import React from 'react';

// Type definitions for table data
export interface TableRow {
  [key: string]: string | number | boolean | null;
}

export interface TableColumn {
  key: string;
  label: string;
  format?: (value: any) => string;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

// Format currency values
export const formatCurrency = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(num);
};

// Format percentage values
export const formatPercentage = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  return (num * 100).toFixed(2) + '%';
};

// Format ratio values
export const formatRatio = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  return num.toFixed(2);
};

// Format number with commas
export const formatNumber = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  return num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
};

// Generic Table Component
export const DataTable: React.FC<{
  data: TableRow[];
  columns: TableColumn[];
  title?: string;
  striped?: boolean;
  bordered?: boolean;
  hoverable?: boolean;
}> = ({ data, columns, title, striped = true, bordered = true, hoverable = true }) => {
  if (!data || data.length === 0) {
    return <div className="p-4 text-gray-500 text-center">No data available</div>;
  }

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold text-gray-800 mb-3">{title}</h3>}
      <div className="overflow-x-auto rounded-lg border border-gray-300 shadow">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 font-semibold text-left ${
                    col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : ''
                  }`}
                  style={{ width: col.width }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`
                  ${striped && rowIndex % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
                  ${bordered ? 'border-b border-gray-200' : ''}
                  ${hoverable ? 'hover:bg-indigo-50 transition-colors' : ''}
                `}
              >
                {columns.map((col) => (
                  <td
                    key={`${rowIndex}-${col.key}`}
                    className={`px-4 py-3 text-gray-700 ${
                      col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : ''
                    }`}
                  >
                    {col.format ? col.format(row[col.key]) : String(row[col.key] ?? '-')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Financial Ratios Table Component
export const FinancialRatiosTable: React.FC<{ data: any }> = ({ data }) => {
  if (!data || typeof data !== 'object') {
    return <div className="p-4 text-gray-500">No ratio data available</div>;
  }

  // Handle nested structure from backend
  // Data can come in format: {liquidity_ratios: {...}, profitability_ratios: {...}} or flat {current_ratio: ...}
  let flatData = data;
  
  // If data has nested category objects, flatten them
  if (data.liquidity_ratios || data.profitability_ratios || data.leverage_ratios || data.efficiency_ratios) {
    flatData = {};
    
    if (data.liquidity_ratios && typeof data.liquidity_ratios === 'object') {
      Object.assign(flatData, data.liquidity_ratios);
    }
    if (data.profitability_ratios && typeof data.profitability_ratios === 'object') {
      Object.assign(flatData, data.profitability_ratios);
    }
    if (data.leverage_ratios && typeof data.leverage_ratios === 'object') {
      Object.assign(flatData, data.leverage_ratios);
    }
    if (data.efficiency_ratios && typeof data.efficiency_ratios === 'object') {
      Object.assign(flatData, data.efficiency_ratios);
    }
  }

  const categories: {
    [key: string]: { label: string; ratios: Array<{ key: string; label: string }> };
  } = {
    liquidity: {
      label: '💧 Liquidity Ratios',
      ratios: [
        { key: 'current_ratio', label: 'Current Ratio' },
        { key: 'quick_ratio', label: 'Quick Ratio' },
        { key: 'cash_ratio', label: 'Cash Ratio' },
      ],
    },
    profitability: {
      label: '📈 Profitability Ratios',
      ratios: [
        { key: 'gross_margin', label: 'Gross Margin' },
        { key: 'operating_margin', label: 'Operating Margin' },
        { key: 'net_margin', label: 'Net Margin' },
        { key: 'roa', label: 'Return on Assets (ROA)' },
        { key: 'roe', label: 'Return on Equity (ROE)' },
      ],
    },
    leverage: {
      label: '⚖️ Leverage Ratios',
      ratios: [
        { key: 'debt_ratio', label: 'Debt Ratio' },
        { key: 'debt_to_equity', label: 'Debt to Equity' },
        { key: 'equity_multiplier', label: 'Equity Multiplier' },
        { key: 'interest_coverage', label: 'Interest Coverage' },
      ],
    },
    efficiency: {
      label: '⚡ Efficiency Ratios',
      ratios: [
        { key: 'asset_turnover', label: 'Asset Turnover' },
        { key: 'inventory_turnover', label: 'Inventory Turnover' },
        { key: 'receivables_turnover', label: 'Receivables Turnover' },
        { key: 'payables_turnover', label: 'Payables Turnover' },
      ],
    },
  };

  return (
    <div className="space-y-6 w-full">
      {Object.entries(categories).map(([catKey, category]) => {
        const categoryData = category.ratios
          .filter((ratio) => flatData[ratio.key] !== undefined && flatData[ratio.key] !== null)
          .map((ratio) => ({
            metric: ratio.label,
            value: flatData[ratio.key],
          }));

        if (categoryData.length === 0) return null;

        const columns: TableColumn[] = [
          { key: 'metric', label: 'Metric', width: '60%' },
          { key: 'value', label: 'Value', width: '40%', align: 'right', format: formatRatio },
        ];

        return (
          <div key={catKey}>
            <DataTable
              data={categoryData}
              columns={columns}
              title={category.label}
              striped
              bordered
              hoverable
            />
          </div>
        );
      })}
    </div>
  );
};

// Balance Sheet Table Component
export const BalanceSheetTable: React.FC<{ data: any }> = ({ data }) => {
  if (!data || typeof data !== 'object') {
    return <div className="p-4 text-gray-500">No balance sheet data available</div>;
  }

  // Assets Section
  const assetsData = [];
  if (data.current_assets) assetsData.push({ item: 'Current Assets', amount: data.current_assets });
  if (data.non_current_assets) assetsData.push({ item: 'Non-Current Assets', amount: data.non_current_assets });
  if (data.total_assets) assetsData.push({ item: 'Total Assets', amount: data.total_assets, isBold: true });

  // Liabilities Section
  const liabilitiesData = [];
  if (data.current_liabilities) liabilitiesData.push({ item: 'Current Liabilities', amount: data.current_liabilities });
  if (data.non_current_liabilities) liabilitiesData.push({ item: 'Non-Current Liabilities', amount: data.non_current_liabilities });
  if (data.total_liabilities) liabilitiesData.push({ item: 'Total Liabilities', amount: data.total_liabilities, isBold: true });

  // Equity Section
  const equityData = [];
  if (data.common_stock) equityData.push({ item: 'Common Stock', amount: data.common_stock });
  if (data.retained_earnings) equityData.push({ item: 'Retained Earnings', amount: data.retained_earnings });
  if (data.total_equity) equityData.push({ item: 'Total Equity', amount: data.total_equity, isBold: true });

  const columns: TableColumn[] = [
    { key: 'item', label: 'Item', width: '60%' },
    { key: 'amount', label: 'Amount (₹)', width: '40%', align: 'right', format: formatCurrency },
  ];

  return (
    <div className="space-y-6 w-full">
      {assetsData.length > 0 && (
        <div>
          <DataTable
            data={assetsData}
            columns={columns}
            title="📊 Assets"
            striped
            bordered
            hoverable
          />
        </div>
      )}

      {liabilitiesData.length > 0 && (
        <div>
          <DataTable
            data={liabilitiesData}
            columns={columns}
            title="💳 Liabilities"
            striped
            bordered
            hoverable
          />
        </div>
      )}

      {equityData.length > 0 && (
        <div>
          <DataTable
            data={equityData}
            columns={columns}
            title="💰 Equity"
            striped
            bordered
            hoverable
          />
        </div>
      )}
    </div>
  );
};

// Detect data type and render appropriate table
export const AutoTable: React.FC<{ data: any }> = ({ data }) => {
  if (!data || typeof data !== 'object') {
    return <div className="p-4 text-gray-500">No data to display</div>;
  }

  // Normalize wrapped responses from backend
  let displayData = data;
  
  // Handle wrapped response format from backend (has "response" key with "ratios" and "status")
  if (data.response && data.balance_sheet_data && typeof data.response === 'object') {
    displayData = data.response;
  }
  
  // Also handle direct wrapping: {ratios: {...}, status: "..."}
  if (data.ratios && data.status && typeof data.ratios === 'object') {
    displayData = data.ratios;
  }

  // Check for financial ratios data
  if (displayData.current_ratio || displayData.gross_margin || displayData.debt_ratio || 
      displayData.liquidity_ratios || displayData.profitability_ratios || displayData.leverage_ratios) {
    return <FinancialRatiosTable data={displayData} />;
  }

  // Check for balance sheet data
  if (displayData.total_assets || displayData.current_assets || displayData.total_liabilities) {
    return <BalanceSheetTable data={displayData} />;
  }

  // Fallback for other data structures
  const entries = Object.entries(displayData)
    .filter(([, value]) => {
      // Skip if value is a complex object (unless it's a metric object)
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Check if it looks like a metrics object with numeric values
        const vals = Object.values(value as any);
        return vals.some(v => typeof v === 'number');
      }
      return typeof value !== 'object';
    })
    .map(([key, value]) => ({
      key,
      value: String(value),
    }));

  const columns: TableColumn[] = [
    { key: 'key', label: 'Key' },
    { key: 'value', label: 'Value' },
  ];

  return <DataTable data={entries} columns={columns} />;
};
