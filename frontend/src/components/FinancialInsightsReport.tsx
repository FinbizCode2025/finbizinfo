import React, { useState } from 'react';

interface FinancialInsightsReportProps {
  ratios: any;
  complianceReport?: string;
  auditorReport?: string;
  directorReport?: string;
  summary?: string;
}

const FinancialInsightsReport: React.FC<FinancialInsightsReportProps> = ({
  ratios,
  complianceReport,
  auditorReport,
  directorReport,
  summary,
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Analyze ratios to generate insights
  const generateInsights = () => {
    const insights = {
      liquidity: [] as string[],
      profitability: [] as string[],
      leverage: [] as string[],
      efficiency: [] as string[],
    };

    // Liquidity analysis
    if (ratios.current_ratio) {
      if (ratios.current_ratio > 2) {
        insights.liquidity.push('✓ Strong current ratio indicates excellent short-term liquidity');
      } else if (ratios.current_ratio > 1.5) {
        insights.liquidity.push('✓ Healthy current ratio shows good ability to meet short-term obligations');
      } else if (ratios.current_ratio > 1) {
        insights.liquidity.push('⚠ Current ratio is borderline - monitor cash flow closely');
      } else {
        insights.liquidity.push('✗ Current ratio below 1.0 indicates potential liquidity issues');
      }
    }

    if (ratios.quick_ratio) {
      if (ratios.quick_ratio > 1) {
        insights.liquidity.push('✓ Quick ratio above 1.0 shows strong immediate liquidity');
      } else if (ratios.quick_ratio > 0.5) {
        insights.liquidity.push('✓ Quick ratio indicates reasonable access to liquid assets');
      } else {
        insights.liquidity.push('⚠ Low quick ratio suggests dependency on inventory conversion');
      }
    }

    // Profitability analysis
    if (ratios.net_margin) {
      if (ratios.net_margin > 15) {
        insights.profitability.push('✓ Excellent net profit margin indicates strong profitability');
      } else if (ratios.net_margin > 10) {
        insights.profitability.push('✓ Good net profit margin shows healthy profit generation');
      } else if (ratios.net_margin > 5) {
        insights.profitability.push('✓ Moderate net profit margin is acceptable for most industries');
      } else {
        insights.profitability.push('⚠ Low net profit margin may indicate cost control issues');
      }
    }

    if (ratios.roa) {
      if (ratios.roa > 10) {
        insights.profitability.push('✓ Strong ROA indicates efficient use of assets');
      } else if (ratios.roa > 5) {
        insights.profitability.push('✓ Decent ROA shows reasonable asset productivity');
      } else {
        insights.profitability.push('⚠ Low ROA suggests opportunities for asset utilization improvement');
      }
    }

    if (ratios.roe) {
      if (ratios.roe > 15) {
        insights.profitability.push('✓ Strong ROE delivers excellent returns to shareholders');
      } else if (ratios.roe > 10) {
        insights.profitability.push('✓ Good ROE shows satisfactory returns on shareholder equity');
      } else {
        insights.profitability.push('⚠ Low ROE may warrant review of capital efficiency');
      }
    }

    // Leverage analysis
    if (ratios.debt_ratio) {
      if (ratios.debt_ratio < 0.3) {
        insights.leverage.push('✓ Low debt ratio indicates conservative capital structure');
      } else if (ratios.debt_ratio < 0.5) {
        insights.leverage.push('✓ Moderate debt ratio shows balanced financing');
      } else if (ratios.debt_ratio < 0.7) {
        insights.leverage.push('⚠ High debt ratio indicates significant leverage');
      } else {
        insights.leverage.push('✗ Very high debt ratio presents financial risk');
      }
    }

    if (ratios.debt_to_equity) {
      if (ratios.debt_to_equity < 0.5) {
        insights.leverage.push('✓ Strong debt-to-equity ratio shows solid equity base');
      } else if (ratios.debt_to_equity < 1) {
        insights.leverage.push('✓ Balanced debt-to-equity ratio is healthy');
      } else if (ratios.debt_to_equity < 1.5) {
        insights.leverage.push('⚠ High debt-to-equity ratio increases financial risk');
      } else {
        insights.leverage.push('✗ Very high debt-to-equity ratio is concerning');
      }
    }

    if (ratios.interest_coverage) {
      if (ratios.interest_coverage > 5) {
        insights.leverage.push('✓ Strong interest coverage indicates safe debt servicing');
      } else if (ratios.interest_coverage > 2.5) {
        insights.leverage.push('✓ Adequate interest coverage shows ability to meet interest obligations');
      } else if (ratios.interest_coverage > 1.5) {
        insights.leverage.push('⚠ Tight interest coverage requires monitoring');
      } else {
        insights.leverage.push('✗ Poor interest coverage indicates debt service risk');
      }
    }

    // Efficiency analysis
    if (ratios.asset_turnover) {
      if (ratios.asset_turnover > 2) {
        insights.efficiency.push('✓ High asset turnover shows excellent asset utilization');
      } else if (ratios.asset_turnover > 1) {
        insights.efficiency.push('✓ Good asset turnover indicates efficient operations');
      } else {
        insights.efficiency.push('⚠ Low asset turnover suggests underutilized assets');
      }
    }

    if (ratios.inventory_turnover) {
      if (ratios.inventory_turnover > 8) {
        insights.efficiency.push('✓ High inventory turnover shows efficient inventory management');
      } else if (ratios.inventory_turnover > 4) {
        insights.efficiency.push('✓ Moderate inventory turnover is reasonable');
      } else {
        insights.efficiency.push('⚠ Low inventory turnover may indicate slow-moving inventory');
      }
    }

    return insights;
  };

  const insights = generateInsights();

  const InsightCard = ({ category, icon, title }: { category: keyof typeof insights; icon: string; title: string }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <span className="text-2xl mr-2">{icon}</span>
        {title}
      </h3>
      <ul className="space-y-2">
        {insights[category].length > 0 ? (
          insights[category].map((insight, idx) => (
            <li key={idx} className="text-gray-700 text-sm leading-relaxed flex items-start">
              <span className="mr-3 text-lg flex-shrink-0">
                {insight.includes('✓') && '✓'}
                {insight.includes('⚠') && '⚠'}
                {insight.includes('✗') && '✗'}
              </span>
              <span>{insight.replace(/^[✓⚠✗]\s*/, '')}</span>
            </li>
          ))
        ) : (
          <li className="text-gray-500">No data available</li>
        )}
      </ul>
    </div>
  );

  const ReportSection = ({ title, content }: { title: string; content?: string }) => (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800 border-b-2 border-blue-500 pb-3">{title}</h2>
      {content ? (
        <div className="bg-white p-6 rounded-lg shadow-md prose prose-sm max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{content}</p>
        </div>
      ) : (
        <div className="bg-gray-100 p-6 rounded-lg text-gray-600">No report data available</div>
      )}
    </div>
  );

  return (
    <div className="space-y-6 w-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-8 rounded-lg shadow-lg">
        <h1 className="text-4xl font-bold mb-2">📊 Financial Insights & Analysis Report</h1>
        <p className="text-blue-100">Complete financial health assessment with detailed recommendations</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-gray-300">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'overview'
              ? 'border-b-4 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          📈 Overview
        </button>
        <button
          onClick={() => setActiveTab('compliance')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'compliance'
              ? 'border-b-4 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          ✓ Compliance Report
        </button>
        <button
          onClick={() => setActiveTab('auditor')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'auditor'
              ? 'border-b-4 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          📋 Auditor Report
        </button>
        <button
          onClick={() => setActiveTab('director')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'director'
              ? 'border-b-4 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          👔 Director Report
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'summary'
              ? 'border-b-4 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          📄 Summary
        </button>
      </div>

      {/* Content Sections */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <InsightCard category="liquidity" icon="💧" title="Liquidity Analysis" />
              <InsightCard category="profitability" icon="📈" title="Profitability Analysis" />
              <InsightCard category="leverage" icon="⚖️" title="Leverage Analysis" />
              <InsightCard category="efficiency" icon="⚡" title="Efficiency Analysis" />
            </div>

            {/* Key Metrics Summary */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 p-8 rounded-lg border-2 border-green-300">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">📊 Key Metrics Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {ratios.current_ratio && (
                  <div className="bg-white p-4 rounded shadow">
                    <p className="text-gray-600 text-sm font-semibold">Current Ratio</p>
                    <p className="text-2xl font-bold text-blue-600">{ratios.current_ratio.toFixed(2)}</p>
                  </div>
                )}
                {ratios.net_margin && (
                  <div className="bg-white p-4 rounded shadow">
                    <p className="text-gray-600 text-sm font-semibold">Net Margin</p>
                    <p className="text-2xl font-bold text-blue-600">{(ratios.net_margin * 100).toFixed(2)}%</p>
                  </div>
                )}
                {ratios.debt_ratio && (
                  <div className="bg-white p-4 rounded shadow">
                    <p className="text-gray-600 text-sm font-semibold">Debt Ratio</p>
                    <p className="text-2xl font-bold text-blue-600">{(ratios.debt_ratio * 100).toFixed(2)}%</p>
                  </div>
                )}
                {ratios.roe && (
                  <div className="bg-white p-4 rounded shadow">
                    <p className="text-gray-600 text-sm font-semibold">ROE</p>
                    <p className="text-2xl font-bold text-blue-600">{(ratios.roe * 100).toFixed(2)}%</p>
                  </div>
                )}
              </div>
            </div>

            {/* Detailed Ratios Table */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-bold mb-4">Detailed Financial Ratios</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="px-4 py-2 text-left">Category</th>
                      <th className="px-4 py-2 text-left">Metric</th>
                      <th className="px-4 py-2 text-right">Value</th>
                      <th className="px-4 py-2 text-left">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/** Liquidity **/}
                    {ratios.current_ratio !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2">Liquidity</td>
                        <td className="border-t px-4 py-2">Current Ratio</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.current_ratio !== null ? ratios.current_ratio.toFixed(2) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Higher is better (generally 1.5-3)</td>
                      </tr>
                    )}
                    {ratios.quick_ratio !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Quick Ratio</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.quick_ratio !== null ? ratios.quick_ratio.toFixed(2) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Excludes inventory</td>
                      </tr>
                    )}
                    {ratios.cash_ratio !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Cash Ratio</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.cash_ratio !== null ? ratios.cash_ratio.toFixed(2) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Most conservative liquidity measure</td>
                      </tr>
                    )}

                    {/** Profitability **/}
                    {ratios.gross_profit !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2">Profitability</td>
                        <td className="border-t px-4 py-2">Gross Profit (absolute)</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.gross_profit !== null ? ratios.gross_profit : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Revenue - COGS</td>
                      </tr>
                    )}
                    {ratios.gross_margin !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Gross Margin</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.gross_margin !== null ? (ratios.gross_margin * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Shows markup after direct costs</td>
                      </tr>
                    )}
                    {ratios.operating_profit !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Operating Profit (absolute)</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.operating_profit !== null ? ratios.operating_profit : 'N/A'}</td>
                        <td className="border-t px-4 py-2">EBIT / profit from operations</td>
                      </tr>
                    )}
                    {ratios.operating_margin !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Operating Margin</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.operating_margin !== null ? (ratios.operating_margin * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Operating income / revenue</td>
                      </tr>
                    )}
                    {ratios.net_margin !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2"> </td>
                        <td className="border-t px-4 py-2">Net Margin</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.net_margin !== null ? (ratios.net_margin * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Net income / revenue</td>
                      </tr>
                    )}

                    {/** Returns & Leverage **/}
                    {ratios.roa !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2">Returns</td>
                        <td className="border-t px-4 py-2">Return on Assets (ROA)</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.roa !== null ? (ratios.roa * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Net income / total assets</td>
                      </tr>
                    )}
                    {ratios.roe !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Return on Equity (ROE)</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.roe !== null ? (ratios.roe * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Net income / equity</td>
                      </tr>
                    )}
                    {ratios.debt_ratio !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2">Solvency</td>
                        <td className="border-t px-4 py-2">Debt Ratio</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.debt_ratio !== null ? (ratios.debt_ratio * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Total liabilities / total assets</td>
                      </tr>
                    )}
                    {ratios.debt_to_equity !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Debt to Equity</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.debt_to_equity !== null ? ratios.debt_to_equity.toFixed(2) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Lower is more conservative</td>
                      </tr>
                    )}

                    {/** Efficiency **/}
                    {ratios.asset_turnover !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2">Efficiency</td>
                        <td className="border-t px-4 py-2">Asset Turnover</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.asset_turnover !== null ? ratios.asset_turnover.toFixed(4) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Revenue / total assets</td>
                      </tr>
                    )}
                    {ratios.inventory_turnover !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Inventory Turnover</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.inventory_turnover !== null ? ratios.inventory_turnover.toFixed(4) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">COGS / inventory</td>
                      </tr>
                    )}
                    {ratios.receivables_turnover !== undefined && (
                      <tr>
                        <td className="border-t px-4 py-2" />
                        <td className="border-t px-4 py-2">Receivables Turnover</td>
                        <td className="border-t px-4 py-2 text-right">{ratios.receivables_turnover !== null ? ratios.receivables_turnover.toFixed(4) : 'N/A'}</td>
                        <td className="border-t px-4 py-2">Revenue / receivables</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compliance' && (
          <ReportSection title="Compliance Gap Analysis" content={complianceReport} />
        )}

        {activeTab === 'auditor' && (
          <ReportSection title="Auditor Report" content={auditorReport} />
        )}

        {activeTab === 'director' && (
          <ReportSection title="Director Report & Highlights" content={directorReport} />
        )}

        {activeTab === 'summary' && (
          <ReportSection title="Executive Summary" content={summary} />
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-100 p-6 rounded-lg text-center text-gray-600 text-sm">
        <p>This analysis is based on financial data extracted from uploaded documents.</p>
        <p>Recommendations should be reviewed by financial professionals before making decisions.</p>
      </div>
    </div>
  );
};

export default FinancialInsightsReport;
