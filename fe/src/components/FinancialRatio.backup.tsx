import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './FinancialRatio.css';
import { useAnalysis } from '../context/AnalysisContext';
import BalanceSheetVisualization from './BalanceSheetVisualization';

const FinancialRatio = ({
  endpoint,
  sessionId,
}: {
  endpoint: string;
  sessionId: string;
}) => {
  const [messages, setMessages] = useState<{ text: string; sender: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(true);
  const [comprehensiveBS, setComprehensiveBS] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'breakdown'>('analysis');
  const { setResults } = useAnalysis();
  const [, setMissingInfo] = useState<string>('');

  const formatRatio = (value: number): string => {
    return Number(value).toFixed(2);
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const generateBalanceSheetTable = (comprehensiveData: any): string => {
    if (!comprehensiveData) return '';
    
    let table = '## 📋 Complete Balance Sheet Breakdown\n\n';
    
    const assets = comprehensiveData.assets || {};
    const liabilitiesAndEquity = comprehensiveData.liabilities_and_equity || {};
    
    // Current Assets
    if (assets.current_assets && Object.keys(assets.current_assets.items).length > 0) {
      table += '### 💰 Current Assets\n\n';
      table += '| Item | Amount |\n|------|--------|\n';
      for (const [item, value] of Object.entries(assets.current_assets.items)) {
        const amount = typeof value === 'number' ? formatCurrency(value) : '—';
        table += `| ${item.replace(/_/g, ' ')} | ${amount} |\n`;
      }
      table += `| **Total Current Assets** | **${formatCurrency(assets.current_assets.total)}** |\n\n`;
    }
    
    // Non-Current Assets
    if (assets.non_current_assets && Object.keys(assets.non_current_assets.items).length > 0) {
      table += '### 🏢 Non-Current Assets\n\n';
      table += '| Item | Amount |\n|------|--------|\n';
      for (const [item, value] of Object.entries(assets.non_current_assets.items)) {
        const amount = typeof value === 'number' ? formatCurrency(value) : '—';
        table += `| ${item.replace(/_/g, ' ')} | ${amount} |\n`;
      }
      table += `| **Total Non-Current Assets** | **${formatCurrency(assets.non_current_assets.total)}** |\n`;
      table += `| **TOTAL ASSETS** | **${formatCurrency(assets.total_assets)}** |\n\n`;
    }
    
    // Current Liabilities
    if (liabilitiesAndEquity.current_liabilities && Object.keys(liabilitiesAndEquity.current_liabilities.items).length > 0) {
      table += '### 📊 Current Liabilities\n\n';
      table += '| Item | Amount |\n|------|--------|\n';
      for (const [item, value] of Object.entries(liabilitiesAndEquity.current_liabilities.items)) {
        const amount = typeof value === 'number' ? formatCurrency(value) : '—';
        table += `| ${item.replace(/_/g, ' ')} | ${amount} |\n`;
      }
      table += `| **Total Current Liabilities** | **${formatCurrency(liabilitiesAndEquity.current_liabilities.total)}** |\n\n`;
    }
    
    // Non-Current Liabilities
    if (liabilitiesAndEquity.non_current_liabilities && Object.keys(liabilitiesAndEquity.non_current_liabilities.items).length > 0) {
      table += '### 🏦 Non-Current Liabilities\n\n';
      table += '| Item | Amount |\n|------|--------|\n';
      for (const [item, value] of Object.entries(liabilitiesAndEquity.non_current_liabilities.items)) {
        const amount = typeof value === 'number' ? formatCurrency(value) : '—';
        table += `| ${item.replace(/_/g, ' ')} | ${amount} |\n`;
      }
      table += `| **Total Non-Current Liabilities** | **${formatCurrency(liabilitiesAndEquity.non_current_liabilities.total)}** |\n`;
      table += `| **TOTAL LIABILITIES** | **${formatCurrency(liabilitiesAndEquity.total_liabilities)}** |\n\n`;
    }
    
    // Equity
    if (liabilitiesAndEquity.equity && Object.keys(liabilitiesAndEquity.equity.items).length > 0) {
      table += '### 👥 Shareholders\' Equity\n\n';
      table += '| Item | Amount |\n|------|--------|\n';
      for (const [item, value] of Object.entries(liabilitiesAndEquity.equity.items)) {
        const amount = typeof value === 'number' ? formatCurrency(value) : '—';
        table += `| ${item.replace(/_/g, ' ')} | ${amount} |\n`;
      }
      table += `| **Total Equity** | **${formatCurrency(liabilitiesAndEquity.equity.total)}** |\n`;
      table += `| **TOTAL LIABILITIES & EQUITY** | **${formatCurrency(liabilitiesAndEquity.total_liabilities + liabilitiesAndEquity.equity.total)}** |\n\n`;
    }
    
    return table;
  };

  const generateRatioAnalysis = (response: any): string => {
    let analysis = '# Financial Ratios Analysis\n\n';

    // Handle both direct response and wrapped response formats
    let ratios = response.ratios || response;

    if (response.error || ratios.error) {
      return `## ⚠️ Error\n\n${response.error || ratios.error}`;
    }

    // Check if this is the new detailed structure or legacy structure
    const isDetailedStructure = ratios && typeof ratios === 'object' && 
                               (ratios.liquidity_ratios || ratios.balance_sheet_summary);

    if (!isDetailedStructure) {
      // Legacy format handling - direct flat structure
      analysis = `## Financial Ratios Analysis\n\n`;
      if (ratios.current_ratio) {
        analysis += `### Liquidity Ratios\n\n`;
        analysis += `- **Current Ratio**: ${formatRatio(ratios.current_ratio)}\n`;
        analysis += `  - ${ratios.current_ratio >= 2 ? 'Strong' : ratios.current_ratio >= 1 ? 'Adequate' : 'Weak'} short-term liquidity position\n`;
      }
      if (ratios.quick_ratio) {
        analysis += `- **Quick Ratio**: ${formatRatio(ratios.quick_ratio)}\n`;
        analysis += `  - ${ratios.quick_ratio >= 1 ? 'Good' : 'Potential'} ability to pay short-term obligations\n\n`;
      }
      if (ratios.debt_to_equity || ratios.debt_ratio) {
        analysis += `### Leverage Ratios\n\n`;
        if (ratios.debt_to_equity) {
          analysis += `- **Debt to Equity**: ${formatRatio(ratios.debt_to_equity)}\n`;
          analysis += `  - ${ratios.debt_to_equity <= 1 ? 'Conservative' : ratios.debt_to_equity <= 2 ? 'Moderate' : 'Aggressive'} financial leverage\n`;
        }
        if (ratios.debt_ratio) {
          analysis += `- **Debt Ratio**: ${formatRatio(ratios.debt_ratio)}\n`;
          analysis += `  - ${ratios.debt_ratio <= 0.4 ? 'Low' : ratios.debt_ratio <= 0.6 ? 'Moderate' : 'High'} financial risk\n\n`;
        }
      }
      if (ratios.total_assets || ratios.total_equity) {
        analysis += `### Key Metrics\n\n`;
        if (ratios.total_assets) {
          analysis += `- **Total Assets**: ${formatCurrency(ratios.total_assets)}\n`;
        }
        if (ratios.total_equity) {
          analysis += `- **Total Equity**: ${formatCurrency(ratios.total_equity)}\n`;
        }
      }
      return analysis;
    }

    // New detailed structure handling
    const r = ratios;

    // Balance Sheet Summary
    if (r.balance_sheet_summary && Object.keys(r.balance_sheet_summary).length > 0) {
      analysis += `## 📊 Balance Sheet Summary\n\n`;
      const bs = r.balance_sheet_summary;
      
      if (bs.total_assets) {
        analysis += `**Total Assets**: ₹${(bs.total_assets / 1000000).toFixed(2)}M\n\n`;
      }
      
      analysis += `| Component | Amount |\n`;
      analysis += `|-----------|--------|\n`;
      if (bs.current_assets) {
        analysis += `| Current Assets | ₹${(bs.current_assets / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.non_current_assets) {
        analysis += `| Non-Current Assets | ₹${(bs.non_current_assets / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.total_liabilities) {
        analysis += `| Total Liabilities | ₹${(bs.total_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.current_liabilities) {
        analysis += `| Current Liabilities | ₹${(bs.current_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.non_current_liabilities) {
        analysis += `| Non-Current Liabilities | ₹${(bs.non_current_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.total_equity) {
        analysis += `| Total Equity | ₹${(bs.total_equity / 1000000).toFixed(2)}M |\n`;
      }
      analysis += `\n`;
    }

    // Liquidity Ratios
    if (r.liquidity_ratios && Object.keys(r.liquidity_ratios).length > 0) {
      analysis += `## 💧 Liquidity Ratios\n\n`;
      analysis += `**Measures the company's ability to meet short-term obligations.**\n\n`;
      
      const lr = r.liquidity_ratios;
      const interp = r.interpretation || {};

      if (lr.current_ratio !== undefined) {
        const crValue = lr.current_ratio.toFixed(2);
        analysis += `- **Current Ratio**: ${crValue}\n`;
        analysis += `  - Status: **${interp.current_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: For every ₹1 of current liabilities, the company has ₹${crValue} in current assets\n`;
        analysis += `  - Benchmark: Healthy ratio is 1.5 - 3.0\n\n`;
      }

      if (lr.quick_ratio !== undefined) {
        const qrValue = lr.quick_ratio.toFixed(2);
        analysis += `- **Quick Ratio (Acid Test)**: ${qrValue}\n`;
        analysis += `  - Status: **${interp.quick_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: Excludes inventory; tests immediate liquidity\n`;
        analysis += `  - Benchmark: Healthy ratio is 0.8 - 1.5\n\n`;
      }

      if (lr.cash_ratio !== undefined) {
        analysis += `- **Cash Ratio**: ${lr.cash_ratio.toFixed(2)}\n`;
        analysis += `  - Most conservative measure of liquidity\n\n`;
      }
    }

    // Solvency Ratios
    if (r.solvency_ratios && Object.keys(r.solvency_ratios).length > 0) {
      analysis += `## 🏦 Solvency Ratios\n\n`;
      analysis += `**Measures the company's long-term financial stability and ability to meet long-term obligations.**\n\n`;
      
      const sr = r.solvency_ratios;
      const interp = r.interpretation || {};

      if (sr.debt_to_equity !== undefined) {
        const dteValue = sr.debt_to_equity.toFixed(2);
        analysis += `- **Debt-to-Equity Ratio**: ${dteValue}\n`;
        analysis += `  - Status: **${interp.debt_to_equity || 'Moderate'}**\n`;
        analysis += `  - Interpretation: For every ₹1 of equity, the company has ₹${dteValue} in debt\n`;
        analysis += `  - Benchmark: Conservative <1.0, Moderate 1.0-2.0, Aggressive >2.0\n\n`;
      }

      if (sr.debt_ratio !== undefined) {
        const drValue = sr.debt_ratio.toFixed(2);
        analysis += `- **Debt Ratio**: ${drValue}\n`;
        analysis += `  - Status: **${interp.debt_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: ${(sr.debt_ratio * 100).toFixed(1)}% of assets are financed by debt\n`;
        analysis += `  - Benchmark: Low risk <40%, Moderate 40-60%, High risk >60%\n\n`;
      }

      if (sr.equity_ratio !== undefined) {
        analysis += `- **Equity Ratio**: ${sr.equity_ratio.toFixed(2)}\n`;
        analysis += `  - Status: **${interp.equity_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: ${(sr.equity_ratio * 100).toFixed(1)}% of assets are financed by equity\n`;
        analysis += `  - Benchmark: Strong >50%, Fair 30-50%, Weak <30%\n\n`;
      }
    }

    // Capital Structure Ratios
    if (r.capital_structure_ratios && Object.keys(r.capital_structure_ratios).length > 0) {
      analysis += `## 🏗️ Capital Structure Ratios\n\n`;
      analysis += `**Analyzes how the company's assets are financed through debt and equity.**\n\n`;
      
      const csr = r.capital_structure_ratios;

      if (csr.equity_multiplier !== undefined) {
        analysis += `- **Equity Multiplier**: ${csr.equity_multiplier.toFixed(2)}\n`;
        analysis += `  - How many times total assets exceed equity capital\n\n`;
      }

      if (csr.retention_ratio !== undefined) {
        analysis += `- **Retention Ratio**: ${(csr.retention_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Percentage of earnings retained in the business\n\n`;
      }

      if (csr.long_term_debt_ratio !== undefined) {
        analysis += `- **Long-term Debt Ratio**: ${csr.long_term_debt_ratio.toFixed(2)}\n`;
        analysis += `  - Proportion of long-term debt in total liabilities\n\n`;
      }
    }

    // Efficiency Ratios
    if (r.efficiency_ratios && Object.keys(r.efficiency_ratios).length > 0) {
      analysis += `## ⚙️ Efficiency Ratios\n\n`;
      analysis += `**Measures how effectively the company utilizes its assets.**\n\n`;
      
      const er = r.efficiency_ratios;

      if (er.receivables_to_current_assets !== undefined) {
        analysis += `- **Receivables to Current Assets**: ${(er.receivables_to_current_assets * 100).toFixed(2)}%\n`;
        analysis += `  - Proportion of current assets tied up in receivables\n\n`;
      }

      if (er.asset_base !== undefined) {
        analysis += `- **Asset Base**: ₹${(er.asset_base / 1000000).toFixed(2)}M\n\n`;
      }
    }

    // Overall Assessment
    analysis += `## 📋 Overall Assessment\n\n`;
    
    // Calculate overall health score
    let healthScore = 0;
    let maxScore = 0;
    
    if (r.liquidity_ratios?.current_ratio) {
      const cr = r.liquidity_ratios.current_ratio;
      if (cr >= 2) healthScore += 25; else if (cr >= 1.5) healthScore += 20; else if (cr >= 1) healthScore += 15;
      maxScore += 25;
    }
    
    if (r.solvency_ratios?.debt_ratio) {
      const dr = r.solvency_ratios.debt_ratio;
      if (dr <= 0.4) healthScore += 25; else if (dr <= 0.6) healthScore += 20; else healthScore += 10;
      maxScore += 25;
    }
    
    if (r.solvency_ratios?.equity_ratio) {
      const er = r.solvency_ratios.equity_ratio;
      if (er >= 0.5) healthScore += 25; else if (er >= 0.3) healthScore += 20; else healthScore += 10;
      maxScore += 25;
    }
    
    if (maxScore > 0) {
      const scoreNum = (healthScore / maxScore * 100);
      const score = scoreNum.toFixed(0);
      analysis += `**Financial Health Score**: ${score}%\n\n`;
      
      if (scoreNum >= 80) {
        analysis += `✅ **Strong financial position** - The company demonstrates good liquidity and solvency metrics.\n\n`;
      } else if (scoreNum >= 60) {
        analysis += `⚠️ **Moderate financial position** - Some areas for improvement in liquidity or debt management.\n\n`;
      } else {
        analysis += `❌ **Weak financial position** - Concerns about liquidity or high financial leverage.\n\n`;
      }
    }

    analysis += `**Status**: ${response.status || ratios.status || 'Analysis complete'}\n`;

    return analysis;
  };

  const handleAnalyzeFromFAISS = async () => {
    setMessages([]);
    setMissingInfo('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://127.0.0.1:5002${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const data = await response.json();

      if (response.ok && data.response) {
        // Generate formatted analysis from the ratios
        const analysisText = generateRatioAnalysis(data.response);
        
        setMessages([{ text: analysisText, sender: 'bot' }]);
        setComprehensiveBS(data.comprehensive_balance_sheet);
        setResults((prev: any) => ({ ...prev, financial: data.response }));
        setShowResponse(true);
      } else {
        const errorMessage = data.error || `Analysis failed with status: ${response.status}`;
        setMessages([{ text: `## Error\n\n❌ ${errorMessage}`, sender: 'bot' }]);
        setShowResponse(true);
      }
    } catch (error) {
      setMessages([
        {
          text: `## Error\n\n❌ Could not connect to server. ${error instanceof Error ? error.message : 'Unknown error'}`,
          sender: 'bot',
        },
      ]);
      setShowResponse(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="financial_statement">
        <div className="font-bold text-center text-black-600 mb-8">
          <h2 style={{ color: '#2c3e50', fontSize: '24px', marginBottom: '20px', fontWeight: '700' }}>
            📊 Financial Ratios Analysis
          </h2>
          <button
            onClick={handleAnalyzeFromFAISS}
            disabled={isLoading}
            style={{
              background: isLoading ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: 'white',
              padding: '14px 32px',
              fontSize: '16px',
              fontWeight: '600',
              borderRadius: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: isLoading ? 'none' : '0 4px 15px rgba(102, 126, 234, 0.4)',
              transform: isLoading ? 'none' : 'translateY(0)',
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
              }
            }}
          >
            {isLoading ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <span
                  className="loading-ring"
                  style={{ 
                    display: 'inline-block', 
                    width: '20px', 
                    height: '20px', 
                    borderRadius: '50%',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTop: '2px solid white',
                    animation: 'spin 1s linear infinite'
                  }}
                ></span>
                Analyzing...
              </span>
            ) : (
              '📈 Analyze Financial Ratios'
            )}
          </button>
        </div>

        {messages.length > 0 && (
          <div className="text-right mb-4" style={{ paddingRight: '10px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setActiveTab(activeTab === 'analysis' ? 'breakdown' : 'analysis')}
              style={{
                padding: '8px 16px',
                background: activeTab === 'breakdown' ? '#667eea' : '#764ba2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.9';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
            >
              {activeTab === 'breakdown' ? '📊 Balance Sheet Breakdown' : '📈 Ratio Analysis'}
            </button>
            <button
              onClick={() => setShowResponse((prev) => !prev)}
              style={{
                padding: '8px 16px',
                background: showResponse ? '#667eea' : '#764ba2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.9';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
            >
              {showResponse ? '👁️ Hide' : '👁️ Show'}
            </button>
          </div>
        )}

        {messages.length > 0 && showResponse && (
          <div className="response">
            <div
              style={{
                background: '#f8f9fc',
                border: '1px solid #e0e7ff',
                borderRadius: '12px',
                padding: '20px',
                maxHeight: '70vh',
                overflowY: 'auto',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.15)',
              }}
            >
              {activeTab === 'analysis' ? (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`message ${msg.sender === 'bot' ? 'bot-message' : ''}`}
                    style={{
                      background: msg.sender === 'bot' ? 'white' : '#f0f4ff',
                      borderLeft: `5px solid ${msg.sender === 'bot' ? '#667eea' : '#764ba2'}`,
                      borderRadius: '8px',
                      padding: '16px',
                      marginBottom: '16px',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                    }}
                  >
                    <div className="bot-message-markdown">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  </div>
                ))
              ) : (
                <div
                  style={{
                    background: 'white',
                    borderLeft: '5px solid #667eea',
                    borderRadius: '8px',
                    padding: '16px',
                    marginBottom: '16px',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                  }}
                >
                  <div className="bot-message-markdown">
                    <ReactMarkdown>{generateBalanceSheetTable(comprehensiveBS)}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialRatio;

  const formatRatio = (value: number): string => {
    return Number(value).toFixed(2);
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const generateRatioAnalysis = (response: any): string => {
    let analysis = '# Financial Ratios Analysis\n\n';

    // Handle both direct response and wrapped response formats
    let ratios = response.ratios || response;

    if (response.error || ratios.error) {
      return `## ⚠️ Error\n\n${response.error || ratios.error}`;
    }

    // Check if this is the new detailed structure or legacy structure
    const isDetailedStructure = ratios && typeof ratios === 'object' && 
                               (ratios.liquidity_ratios || ratios.balance_sheet_summary);

    if (!isDetailedStructure) {
      // Legacy format handling - direct flat structure
      analysis = `## Financial Ratios Analysis\n\n`;
      if (ratios.current_ratio) {
        analysis += `### Liquidity Ratios\n\n`;
        analysis += `- **Current Ratio**: ${formatRatio(ratios.current_ratio)}\n`;
        analysis += `  - ${ratios.current_ratio >= 2 ? 'Strong' : ratios.current_ratio >= 1 ? 'Adequate' : 'Weak'} short-term liquidity position\n`;
      }
      if (ratios.quick_ratio) {
        analysis += `- **Quick Ratio**: ${formatRatio(ratios.quick_ratio)}\n`;
        analysis += `  - ${ratios.quick_ratio >= 1 ? 'Good' : 'Potential'} ability to pay short-term obligations\n\n`;
      }
      if (ratios.debt_to_equity || ratios.debt_ratio) {
        analysis += `### Leverage Ratios\n\n`;
        if (ratios.debt_to_equity) {
          analysis += `- **Debt to Equity**: ${formatRatio(ratios.debt_to_equity)}\n`;
          analysis += `  - ${ratios.debt_to_equity <= 1 ? 'Conservative' : ratios.debt_to_equity <= 2 ? 'Moderate' : 'Aggressive'} financial leverage\n`;
        }
        if (ratios.debt_ratio) {
          analysis += `- **Debt Ratio**: ${formatRatio(ratios.debt_ratio)}\n`;
          analysis += `  - ${ratios.debt_ratio <= 0.4 ? 'Low' : ratios.debt_ratio <= 0.6 ? 'Moderate' : 'High'} financial risk\n\n`;
        }
      }
      if (ratios.total_assets || ratios.total_equity) {
        analysis += `### Key Metrics\n\n`;
        if (ratios.total_assets) {
          analysis += `- **Total Assets**: ${formatCurrency(ratios.total_assets)}\n`;
        }
        if (ratios.total_equity) {
          analysis += `- **Total Equity**: ${formatCurrency(ratios.total_equity)}\n`;
        }
      }
      return analysis;
    }

    // New detailed structure handling
    const r = ratios;

    // Balance Sheet Summary
    if (r.balance_sheet_summary && Object.keys(r.balance_sheet_summary).length > 0) {
      analysis += `## 📊 Balance Sheet Summary\n\n`;
      const bs = r.balance_sheet_summary;
      
      if (bs.total_assets) {
        analysis += `**Total Assets**: ₹${(bs.total_assets / 1000000).toFixed(2)}M\n\n`;
      }
      
      analysis += `| Component | Amount |\n`;
      analysis += `|-----------|--------|\n`;
      if (bs.current_assets) {
        analysis += `| Current Assets | ₹${(bs.current_assets / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.non_current_assets) {
        analysis += `| Non-Current Assets | ₹${(bs.non_current_assets / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.total_liabilities) {
        analysis += `| Total Liabilities | ₹${(bs.total_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.current_liabilities) {
        analysis += `| Current Liabilities | ₹${(bs.current_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.non_current_liabilities) {
        analysis += `| Non-Current Liabilities | ₹${(bs.non_current_liabilities / 1000000).toFixed(2)}M |\n`;
      }
      if (bs.total_equity) {
        analysis += `| Total Equity | ₹${(bs.total_equity / 1000000).toFixed(2)}M |\n`;
      }
      analysis += `\n`;
    }

    // Liquidity Ratios
    if (r.liquidity_ratios && Object.keys(r.liquidity_ratios).length > 0) {
      analysis += `## 💧 Liquidity Ratios\n\n`;
      analysis += `**Measures the company's ability to meet short-term obligations.**\n\n`;
      
      const lr = r.liquidity_ratios;
      const interp = r.interpretation || {};

      if (lr.current_ratio !== undefined) {
        const crValue = lr.current_ratio.toFixed(2);
        analysis += `- **Current Ratio**: ${crValue}\n`;
        analysis += `  - Status: **${interp.current_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: For every ₹1 of current liabilities, the company has ₹${crValue} in current assets\n`;
        analysis += `  - Benchmark: Healthy ratio is 1.5 - 3.0\n\n`;
      }

      if (lr.quick_ratio !== undefined) {
        const qrValue = lr.quick_ratio.toFixed(2);
        analysis += `- **Quick Ratio (Acid Test)**: ${qrValue}\n`;
        analysis += `  - Status: **${interp.quick_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: Excludes inventory; tests immediate liquidity\n`;
        analysis += `  - Benchmark: Healthy ratio is 0.8 - 1.5\n\n`;
      }

      if (lr.cash_ratio !== undefined) {
        analysis += `- **Cash Ratio**: ${lr.cash_ratio.toFixed(2)}\n`;
        analysis += `  - Most conservative measure of liquidity\n\n`;
      }
    }

    // Solvency Ratios
    if (r.solvency_ratios && Object.keys(r.solvency_ratios).length > 0) {
      analysis += `## 🏦 Solvency Ratios\n\n`;
      analysis += `**Measures the company's long-term financial stability and ability to meet long-term obligations.**\n\n`;
      
      const sr = r.solvency_ratios;
      const interp = r.interpretation || {};

      if (sr.debt_to_equity !== undefined) {
        const dteValue = sr.debt_to_equity.toFixed(2);
        analysis += `- **Debt-to-Equity Ratio**: ${dteValue}\n`;
        analysis += `  - Status: **${interp.debt_to_equity || 'Moderate'}**\n`;
        analysis += `  - Interpretation: For every ₹1 of equity, the company has ₹${dteValue} in debt\n`;
        analysis += `  - Benchmark: Conservative <1.0, Moderate 1.0-2.0, Aggressive >2.0\n\n`;
      }

      if (sr.debt_ratio !== undefined) {
        const drValue = sr.debt_ratio.toFixed(2);
        analysis += `- **Debt Ratio**: ${drValue}\n`;
        analysis += `  - Status: **${interp.debt_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: ${(sr.debt_ratio * 100).toFixed(1)}% of assets are financed by debt\n`;
        analysis += `  - Benchmark: Low risk <40%, Moderate 40-60%, High risk >60%\n\n`;
      }

      if (sr.equity_ratio !== undefined) {
        analysis += `- **Equity Ratio**: ${sr.equity_ratio.toFixed(2)}\n`;
        analysis += `  - Status: **${interp.equity_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: ${(sr.equity_ratio * 100).toFixed(1)}% of assets are financed by equity\n`;
        analysis += `  - Benchmark: Strong >50%, Fair 30-50%, Weak <30%\n\n`;
      }
    }

    // Capital Structure Ratios
    if (r.capital_structure_ratios && Object.keys(r.capital_structure_ratios).length > 0) {
      analysis += `## 🏗️ Capital Structure Ratios\n\n`;
      analysis += `**Analyzes how the company's assets are financed through debt and equity.**\n\n`;
      
      const csr = r.capital_structure_ratios;

      if (csr.equity_multiplier !== undefined) {
        analysis += `- **Equity Multiplier**: ${csr.equity_multiplier.toFixed(2)}\n`;
        analysis += `  - How many times total assets exceed equity capital\n\n`;
      }

      if (csr.retention_ratio !== undefined) {
        analysis += `- **Retention Ratio**: ${(csr.retention_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Percentage of earnings retained in the business\n\n`;
      }

      if (csr.long_term_debt_ratio !== undefined) {
        analysis += `- **Long-term Debt Ratio**: ${csr.long_term_debt_ratio.toFixed(2)}\n`;
        analysis += `  - Proportion of long-term debt in total liabilities\n\n`;
      }
    }

    // Efficiency Ratios
    if (r.efficiency_ratios && Object.keys(r.efficiency_ratios).length > 0) {
      analysis += `## ⚙️ Efficiency Ratios\n\n`;
      analysis += `**Measures how effectively the company utilizes its assets.**\n\n`;
      
      const er = r.efficiency_ratios;

      if (er.receivables_to_current_assets !== undefined) {
        analysis += `- **Receivables to Current Assets**: ${(er.receivables_to_current_assets * 100).toFixed(2)}%\n`;
        analysis += `  - Proportion of current assets tied up in receivables\n\n`;
      }

      if (er.asset_base !== undefined) {
        analysis += `- **Asset Base**: ₹${(er.asset_base / 1000000).toFixed(2)}M\n\n`;
      }
    }

    // Overall Assessment
    analysis += `## 📋 Overall Assessment\n\n`;
    
    // Calculate overall health score
    let healthScore = 0;
    let maxScore = 0;
    
    if (r.liquidity_ratios?.current_ratio) {
      const cr = r.liquidity_ratios.current_ratio;
      if (cr >= 2) healthScore += 25; else if (cr >= 1.5) healthScore += 20; else if (cr >= 1) healthScore += 15;
      maxScore += 25;
    }
    
    if (r.solvency_ratios?.debt_ratio) {
      const dr = r.solvency_ratios.debt_ratio;
      if (dr <= 0.4) healthScore += 25; else if (dr <= 0.6) healthScore += 20; else healthScore += 10;
      maxScore += 25;
    }
    
    if (r.solvency_ratios?.equity_ratio) {
      const er = r.solvency_ratios.equity_ratio;
      if (er >= 0.5) healthScore += 25; else if (er >= 0.3) healthScore += 20; else healthScore += 10;
      maxScore += 25;
    }
    
    if (maxScore > 0) {
      const scoreNum = (healthScore / maxScore * 100);
      const score = scoreNum.toFixed(0);
      analysis += `**Financial Health Score**: ${score}%\n\n`;
      
      if (scoreNum >= 80) {
        analysis += `✅ **Strong financial position** - The company demonstrates good liquidity and solvency metrics.\n\n`;
      } else if (scoreNum >= 60) {
        analysis += `⚠️ **Moderate financial position** - Some areas for improvement in liquidity or debt management.\n\n`;
      } else {
        analysis += `❌ **Weak financial position** - Concerns about liquidity or high financial leverage.\n\n`;
      }
    }

    analysis += `**Status**: ${response.status || ratios.status || 'Analysis complete'}\n`;

    return analysis;
  };

  const handleAnalyzeFromFAISS = async () => {
    setMessages([]);
    setMissingInfo('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://127.0.0.1:5002${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const data = await response.json();

      if (response.ok && data.response) {
        // Generate formatted analysis from the ratios
        const analysisText = generateRatioAnalysis(data.response);
        
        setMessages([{ text: analysisText, sender: 'bot' }]);
        setResults((prev: any) => ({ ...prev, financial: data.response }));
        setShowResponse(true);
      } else {
        const errorMessage = data.error || `Analysis failed with status: ${response.status}`;
        setMessages([{ text: `## Error\n\n❌ ${errorMessage}`, sender: 'bot' }]);
        setShowResponse(true);
      }
    } catch (error) {
      setMessages([
        {
          text: `## Error\n\n❌ Could not connect to server. ${error instanceof Error ? error.message : 'Unknown error'}`,
          sender: 'bot',
        },
      ]);
      setShowResponse(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="financial_statement">
        <div className="font-bold text-center text-black-600 mb-8">
          <h2 style={{ color: '#2c3e50', fontSize: '24px', marginBottom: '20px', fontWeight: '700' }}>
            📊 Financial Ratios Analysis
          </h2>
          <button
            onClick={handleAnalyzeFromFAISS}
            disabled={isLoading}
            style={{
              background: isLoading ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: 'white',
              padding: '14px 32px',
              fontSize: '16px',
              fontWeight: '600',
              borderRadius: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: isLoading ? 'none' : '0 4px 15px rgba(102, 126, 234, 0.4)',
              transform: isLoading ? 'none' : 'translateY(0)',
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
              }
            }}
          >
            {isLoading ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <span
                  className="loading-ring"
                  style={{ 
                    display: 'inline-block', 
                    width: '20px', 
                    height: '20px', 
                    borderRadius: '50%',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTop: '2px solid white',
                    animation: 'spin 1s linear infinite'
                  }}
                ></span>
                Analyzing...
              </span>
            ) : (
              '📈 Analyze Financial Ratios'
            )}
          </button>
        </div>

        {messages.length > 0 && (
          <div className="text-right mb-4" style={{ paddingRight: '10px' }}>
            <button
              onClick={() => setShowResponse((prev) => !prev)}
              style={{
                padding: '8px 16px',
                background: showResponse ? '#667eea' : '#764ba2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.9';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
            >
              {showResponse ? '👁️ Hide' : '👁️ Show'}
            </button>
          </div>
        )}

        {messages.length > 0 && showResponse && (
          <div className="response">
            <div
              style={{
                background: '#f8f9fc',
                border: '1px solid #e0e7ff',
                borderRadius: '12px',
                padding: '20px',
                maxHeight: '70vh',
                overflowY: 'auto',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.15)',
              }}
            >
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.sender === 'bot' ? 'bot-message' : ''}`}
                  style={{
                    background: msg.sender === 'bot' ? 'white' : '#f0f4ff',
                    borderLeft: `5px solid ${msg.sender === 'bot' ? '#667eea' : '#764ba2'}`,
                    borderRadius: '8px',
                    padding: '16px',
                    marginBottom: '16px',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                  }}
                >
                  <div className="bot-message-markdown">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Balance Sheet Visualization Component */}
        {comprehensiveBS && <BalanceSheetVisualization comprehensiveBS={comprehensiveBS} />}
      </div>
    </div>
  );
};

export default FinancialRatio;
