import React from 'react';

interface Ratio {
  name: string;
  value: string;
  description: string;
  interpretation?: string;
}

interface FinancialRatiosDisplayProps {
  ratios: Ratio[];
  status: string;
}

const FinancialRatiosDisplay: React.FC<FinancialRatiosDisplayProps> = ({ ratios, status }) => {
  if (!ratios || ratios.length === 0) {
    return (
      <div className="p-4 my-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800 rounded-md shadow-sm">
        <p className="font-bold">No Ratios Available</p>
        <p>{status || 'Could not calculate financial ratios from the document.'}</p>
      </div>
    );
  }

  const getIndicatorColor = (name: string, valueStr: string): string => {
    const value = parseFloat(valueStr);
    if (isNaN(value)) return 'bg-gray-400';

    const lowerIsBetter = ['Debt-to-Equity Ratio', 'Debt Ratio'];
    const higherIsBetter = ['Current Ratio', 'Quick Ratio (Acid-Test)'];

    if (lowerIsBetter.includes(name)) {
      if (value < 1.0) return 'bg-green-500';
      if (value < 2.0) return 'bg-yellow-500';
      return 'bg-red-500';
    }
    if (higherIsBetter.includes(name)) {
      if (value > 2.0) return 'bg-green-500';
      if (value > 1.0) return 'bg-yellow-500';
      return 'bg-red-500';
    }
    return 'bg-blue-500'; // Default for informational values like Total Assets
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 border-b-2 pb-2">Financial Ratios</h2>
      <p className="text-gray-600">{status}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {ratios.map((ratio, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg overflow-hidden transform hover:scale-105 transition-transform duration-300">
            <div className="p-5">
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-semibold text-gray-900">{ratio.name}</h3>
                <span 
                  className={`w-4 h-4 rounded-full ${getIndicatorColor(ratio.name, ratio.value)}`}
                  title={`Indicator for ${ratio.name}`}
                ></span>
              </div>
              <p className="text-4xl font-bold text-indigo-600 my-3">{ratio.value}</p>
              <p className="text-sm text-gray-600">{ratio.description}</p>
              {ratio.interpretation && (
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500 italic">
                    <span className="font-semibold">Interpretation:</span> {ratio.interpretation}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 text-xs text-gray-400">
        <p><strong>Disclaimer:</strong> The color indicators (green/yellow/red) are based on general financial principles and may not apply to all industries or business contexts. They are for informational purposes only.</p>
      </div>
    </div>
  );
};

export default FinancialRatiosDisplay;