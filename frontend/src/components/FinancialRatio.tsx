import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './FinancialRatio.css';
import { useAnalysis } from '../context/AnalysisContext';
import BalanceSheetVisualization from './BalanceSheetVisualization';
import FinancialTableDisplay from './FinancialTableDisplay';

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
  const [displayFormat, setDisplayFormat] = useState<'table' | 'markdown'>('table');
  const [ratioData, setRatioData] = useState<any>(null);
  const [extractionMethod, setExtractionMethod] = useState<string | null>(null);
  const { setResults } = useAnalysis();
  const [, setMissingInfo] = useState<string>('');


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
    let analysis = '# Financial Ratios Analysis (45+ Comprehensive Ratios)\n\n';

    let ratios = response.ratios || response;

    if (response.error || ratios.error) {
      return `## ⚠️ Error\n\n${response.error || ratios.error}`;
    }

    const isDetailedStructure = ratios && typeof ratios === 'object' &&
      (ratios.liquidity_ratios || ratios.balance_sheet_summary);

    if (!isDetailedStructure) {
      return `## Legacy Format\n\n${JSON.stringify(ratios, null, 2)}`;
    }

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
        analysis += `  - Benchmark: Healthy 1.5 - 3.0\n\n`;
      }

      if (lr.quick_ratio !== undefined) {
        const qrValue = lr.quick_ratio.toFixed(2);
        analysis += `- **Quick Ratio (Acid Test)**: ${qrValue}\n`;
        analysis += `  - Status: **${interp.quick_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: Excludes inventory; tests immediate liquidity\n`;
        analysis += `  - Benchmark: Healthy 0.8 - 1.5\n\n`;
      }

      if (lr.cash_ratio !== undefined) {
        analysis += `- **Cash Ratio**: ${lr.cash_ratio.toFixed(2)}\n`;
        analysis += `  - Most conservative measure of liquidity\n`;
        analysis += `  - Benchmark: Good >0.2, Fair 0.1-0.2, Weak <0.1\n\n`;
      }

      if (lr.working_capital !== undefined) {
        analysis += `- **Working Capital**: ₹${(lr.working_capital / 1000000).toFixed(2)}M\n`;
        analysis += `  - Absolute working capital available\n\n`;
      }

      if (lr.working_capital_ratio !== undefined) {
        analysis += `- **Working Capital Ratio**: ${lr.working_capital_ratio.toFixed(2)}\n`;
        analysis += `  - Additional measure of short-term financial health\n\n`;
      }
    }

    // Solvency Ratios
    if (r.solvency_ratios && Object.keys(r.solvency_ratios).length > 0) {
      analysis += `## 🏦 Solvency & Leverage Ratios\n\n`;
      analysis += `**Measures the company's long-term financial stability and debt capacity.**\n\n`;

      const sr = r.solvency_ratios;
      const interp = r.interpretation || {};

      if (sr.debt_to_equity !== undefined) {
        const dteValue = sr.debt_to_equity.toFixed(2);
        analysis += `- **Debt-to-Equity Ratio**: ${dteValue}\n`;
        analysis += `  - Status: **${interp.debt_to_equity || 'Moderate'}**\n`;
        analysis += `  - Interpretation: For every ₹1 of equity, ₹${dteValue} in debt\n`;
        analysis += `  - Benchmark: Conservative <1.0, Moderate 1.0-2.0, Aggressive >2.0\n\n`;
      }

      if (sr.debt_ratio !== undefined) {
        const drValue = sr.debt_ratio.toFixed(2);
        analysis += `- **Debt Ratio**: ${drValue}\n`;
        analysis += `  - Status: **${interp.debt_ratio || 'Moderate'}**\n`;
        analysis += `  - Interpretation: ${(sr.debt_ratio * 100).toFixed(1)}% of assets financed by debt\n`;
        analysis += `  - Benchmark: Low <40%, Moderate 40-60%, High >60%\n\n`;
      }

      if (sr.equity_ratio !== undefined) {
        analysis += `- **Equity Ratio**: ${sr.equity_ratio.toFixed(2)}\n`;
        analysis += `  - Interpretation: ${(sr.equity_ratio * 100).toFixed(1)}% of assets financed by equity\n`;
        analysis += `  - Benchmark: Strong >50%, Fair 30-50%, Weak <30%\n\n`;
      }

      if (sr.interest_coverage !== undefined) {
        analysis += `- **Interest Coverage Ratio**: ${sr.interest_coverage.toFixed(2)}x\n`;
        analysis += `  - Status: **${interp.interest_coverage || 'Fair'}**\n`;
        analysis += `  - Interpretation: Times operating income covers interest\n`;
        analysis += `  - Benchmark: Strong >2.5x, Adequate 1.5-2.5x, Weak <1.5x\n\n`;
      }

      if (sr.debt_service_coverage !== undefined) {
        analysis += `- **Debt Service Coverage Ratio**: ${sr.debt_service_coverage.toFixed(2)}x\n`;
        analysis += `  - Status: **${interp.debt_service_coverage || 'Fair'}**\n`;
        analysis += `  - Interpretation: Operating income covers debt payments ${sr.debt_service_coverage.toFixed(2)}x\n`;
        analysis += `  - Benchmark: Strong >2.5x, Adequate 1.5-2.5x, Weak <1.5x\n\n`;
      }

      if (sr.leverage_ratio !== undefined) {
        analysis += `- **Leverage Ratio**: ${sr.leverage_ratio.toFixed(2)}\n`;
        analysis += `  - Interpretation: Total debt per rupee of equity\n\n`;
      }

      if (sr.long_term_debt_to_equity !== undefined) {
        analysis += `- **Long-term Debt to Equity**: ${sr.long_term_debt_to_equity.toFixed(2)}\n`;
        analysis += `  - Interpretation: Long-term financial leverage\n\n`;
      }

      if (sr.assets_to_liabilities !== undefined) {
        analysis += `- **Assets to Liabilities**: ${sr.assets_to_liabilities.toFixed(2)}\n`;
        analysis += `  - Interpretation: Asset coverage for creditors\n\n`;
      }
    }

    // Capital Structure Ratios
    if (r.capital_structure_ratios && Object.keys(r.capital_structure_ratios).length > 0) {
      analysis += `## 🏗️ Capital Structure Ratios\n\n`;
      analysis += `**Analyzes how the company's assets are financed through debt and equity.**\n\n`;

      const csr = r.capital_structure_ratios;

      if (csr.equity_multiplier !== undefined) {
        analysis += `- **Equity Multiplier**: ${csr.equity_multiplier.toFixed(2)}x\n`;
        analysis += `  - How many times total assets exceed equity capital\n\n`;
      }

      if (csr.retention_ratio !== undefined) {
        analysis += `- **Retention Ratio**: ${(csr.retention_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Percentage of earnings retained in business\n\n`;
      }

      if (csr.long_term_debt_ratio !== undefined) {
        analysis += `- **Long-term Debt Ratio**: ${csr.long_term_debt_ratio.toFixed(2)}\n`;
        analysis += `  - Proportion of long-term debt in total liabilities\n\n`;
      }

      if (csr.debt_to_assets !== undefined) {
        analysis += `- **Debt to Assets**: ${csr.debt_to_assets.toFixed(2)}\n`;
        analysis += `  - Interpretation: Asset financing from debt sources\n\n`;
      }

      if (csr.equity_to_debt !== undefined) {
        analysis += `- **Equity to Debt**: ${csr.equity_to_debt.toFixed(2)}\n`;
        analysis += `  - Interpretation: Equity financing relative to debt\n\n`;
      }
    }

    // Profitability Ratios
    if (r.profitability_ratios && Object.keys(r.profitability_ratios).length > 0) {
      analysis += `## 📈 Profitability Ratios\n\n`;
      analysis += `**Measures how effectively the company generates profit.**\n\n`;

      const pr = r.profitability_ratios;
      const interp = r.interpretation || {};

      if (pr.gross_margin !== undefined) {
        analysis += `- **Gross Profit Margin**: ${pr.gross_margin.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.gross_margin || 'Fair'}**\n`;
        analysis += `  - Benchmark: Excellent >40%, Good 30-40%, Fair 20-30%, Weak <20%\n\n`;
      }

      if (pr.operating_margin !== undefined) {
        analysis += `- **Operating Profit Margin**: ${pr.operating_margin.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.operating_margin || 'Fair'}**\n`;
        analysis += `  - Benchmark: Excellent >15%, Good 10-15%, Fair 5-10%, Weak <5%\n\n`;
      }

      if (pr.ebitda_margin !== undefined) {
        analysis += `- **EBITDA Margin**: ${pr.ebitda_margin.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.ebitda_margin || 'Fair'}**\n`;
        analysis += `  - Operating profitability before interest, taxes, D&A\n\n`;
      }

      if (pr.ebit_margin !== undefined) {
        analysis += `- **EBIT Margin**: ${pr.ebit_margin.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.ebit_margin || 'Fair'}**\n`;
        analysis += `  - Operating profit margin\n\n`;
      }

      if (pr.net_margin !== undefined) {
        analysis += `- **Net Profit Margin**: ${pr.net_margin.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.net_margin || 'Fair'}**\n`;
        analysis += `  - Bottom-line profitability after all expenses\n`;
        analysis += `  - Benchmark: Excellent >10%, Good 7-10%, Fair 3-7%, Weak <3%\n\n`;
      }

      if (pr.return_on_sales !== undefined) {
        analysis += `- **Return on Sales (ROS)**: ${pr.return_on_sales.toFixed(2)}%\n`;
        analysis += `  - Net income per rupee of sales\n\n`;
      }

      if (pr.roa !== undefined) {
        analysis += `- **Return on Assets (ROA)**: ${pr.roa.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.roa || 'Fair'}**\n`;
        analysis += `  - Benchmark: Excellent >10%, Good 5-10%, Fair 2-5%, Weak <2%\n\n`;
      }

      if (pr.roe !== undefined) {
        analysis += `- **Return on Equity (ROE)**: ${pr.roe.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.roe || 'Fair'}**\n`;
        analysis += `  - Benchmark: Excellent >20%, Good 15-20%, Fair 10-15%, Weak <10%\n\n`;
      }
    }

    // Activity & Turnover Ratios
    if (r.activity_ratios && Object.keys(r.activity_ratios).length > 0) {
      analysis += `## 🔄 Activity & Turnover Ratios\n\n`;
      analysis += `**Measures how efficiently the company uses assets to generate revenue.**\n\n`;

      const ar = r.activity_ratios;
      const interp = r.interpretation || {};

      if (ar.asset_turnover !== undefined) {
        analysis += `- **Asset Turnover Ratio**: ${ar.asset_turnover.toFixed(2)}x\n`;
        analysis += `  - Status: **${interp.asset_turnover || 'Fair'}**\n`;
        analysis += `  - For every ₹1 of assets, generates ₹${ar.asset_turnover.toFixed(2)} revenue\n`;
        analysis += `  - Benchmark: Excellent >2.0x, Good 1.5-2.0x, Fair 1.0-1.5x\n\n`;
      }

      if (ar.fixed_asset_turnover !== undefined) {
        analysis += `- **Fixed Asset Turnover**: ${ar.fixed_asset_turnover.toFixed(2)}x\n`;
        analysis += `  - Status: **${interp.fixed_asset_turnover || 'Fair'}**\n`;
        analysis += `  - Revenue per rupee of fixed assets\n\n`;
      }

      if (ar.current_asset_turnover !== undefined) {
        analysis += `- **Current Asset Turnover**: ${ar.current_asset_turnover.toFixed(2)}x\n`;
        analysis += `  - Efficiency of current assets in generating sales\n\n`;
      }

      if (ar.receivables_turnover !== undefined) {
        analysis += `- **Receivables Turnover**: ${ar.receivables_turnover.toFixed(2)}x/year\n`;
        analysis += `  - Status: **${interp.receivables_turnover || 'Fair'}**\n`;
        analysis += `  - Collections per year\n`;
        analysis += `  - Benchmark: Higher is better; 6-12x typical\n\n`;
      }

      if (ar.days_sales_outstanding !== undefined) {
        analysis += `- **Days Sales Outstanding (DSO)**: ${ar.days_sales_outstanding.toFixed(0)} days\n`;
        analysis += `  - Average days to collect payments\n`;
        analysis += `  - Benchmark: Lower is better; 30-45 days good\n\n`;
      }
    }

    // DuPont Analysis
    if (r.dupont_analysis && Object.keys(r.dupont_analysis).length > 0) {
      analysis += `## 🔍 DuPont Analysis (ROE Decomposition)\n\n`;
      analysis += `**Breaks ROE into profitability, efficiency, and leverage components.**\n\n`;

      const da = r.dupont_analysis;
      const interp = r.interpretation || {};

      if (da.net_profit_margin !== undefined && da.asset_turnover !== undefined && da.equity_multiplier !== undefined) {
        analysis += `**Formula**: ROE = Net Margin × Asset Turnover × Equity Multiplier\n\n`;
        analysis += `- **Net Profit Margin**: ${da.net_profit_margin?.toFixed(2)}%\n`;
        analysis += `  - Component 1: Profitability\n\n`;
        analysis += `- **Asset Turnover**: ${da.asset_turnover?.toFixed(2)}x\n`;
        analysis += `  - Component 2: Efficiency\n\n`;
        analysis += `- **Equity Multiplier**: ${da.equity_multiplier?.toFixed(2)}x\n`;
        analysis += `  - Component 3: Leverage\n\n`;
      }

      if (da.roe_dupont !== undefined) {
        analysis += `- **DuPont ROE**: ${da.roe_dupont.toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.dupont_roe || 'Fair'}**\n`;
        analysis += `  - Calculation: ${da.net_profit_margin?.toFixed(2)}% × ${da.asset_turnover?.toFixed(2)} × ${da.equity_multiplier?.toFixed(2)} = ${da.roe_dupont?.toFixed(2)}%\n`;
        analysis += `  - Identifies which component drives ROE performance\n\n`;
      }
    }

    // Working Capital Ratios
    if (r.working_capital_ratios && Object.keys(r.working_capital_ratios).length > 0) {
      analysis += `## 💼 Working Capital Ratios\n\n`;
      analysis += `**Measures operational efficiency and cash management.**\n\n`;

      const wc = r.working_capital_ratios;
      const interp = r.interpretation || {};

      if (wc.cash_ratio !== undefined) {
        analysis += `- **Cash Ratio**: ${wc.cash_ratio.toFixed(2)}\n`;
        analysis += `  - Status: **${interp.cash_ratio || 'Fair'}**\n`;
        analysis += `  - Most conservative liquidity measure\n`;
        analysis += `  - Benchmark: Good >0.2, Fair 0.1-0.2, Weak <0.1\n\n`;
      }

      if (wc.operating_cash_ratio !== undefined) {
        analysis += `- **Operating Cash Ratio**: ${wc.operating_cash_ratio.toFixed(2)}\n`;
        analysis += `  - Operating efficiency vs short-term obligations\n\n`;
      }
    }

    // Efficiency Ratios
    if (r.efficiency_ratios && Object.keys(r.efficiency_ratios).length > 0) {
      analysis += `## ⚙️ Efficiency Ratios\n\n`;
      analysis += `**Measures asset utilization effectiveness.**\n\n`;

      const er = r.efficiency_ratios;

      if (er.current_assets_ratio !== undefined) {
        analysis += `- **Current Assets Ratio**: ${(er.current_assets_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Percentage of current assets in total assets\n\n`;
      }

      if (er.fixed_assets_ratio !== undefined) {
        analysis += `- **Fixed Assets Ratio**: ${(er.fixed_assets_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Percentage of fixed assets in total assets\n\n`;
      }

      if (er.receivables_to_current_assets !== undefined) {
        analysis += `- **Receivables to Current Assets**: ${(er.receivables_to_current_assets * 100).toFixed(2)}%\n`;
        analysis += `  - Current assets tied up in receivables\n\n`;
      }

      if (er.asset_base !== undefined) {
        analysis += `- **Asset Base**: ₹${(er.asset_base / 1000000).toFixed(2)}M\n\n`;
      }
    }

    // Valuation & Asset Quality Ratios
    if (r.valuation_ratios && Object.keys(r.valuation_ratios).length > 0) {
      analysis += `## 💎 Valuation & Asset Quality Ratios\n\n`;
      analysis += `**Measures asset composition and quality.**\n\n`;

      const vr = r.valuation_ratios;
      const interp = r.interpretation || {};

      if (vr.book_value_ratio !== undefined) {
        analysis += `- **Book Value Ratio**: ${vr.book_value_ratio.toFixed(2)}\n`;
        analysis += `  - Equity per rupee of assets\n\n`;
      }

      if (vr.asset_quality_ratio !== undefined) {
        analysis += `- **Asset Quality Ratio**: ${(vr.asset_quality_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Status: **${interp.asset_quality || 'Fair'}**\n`;
        analysis += `  - Current assets as % of total assets\n`;
        analysis += `  - Benchmark: Good >60%, Fair 40-60%, Weak <40%\n\n`;
      }

      if (vr.liquidity_quality_ratio !== undefined) {
        analysis += `- **Liquidity Quality Ratio**: ${(vr.liquidity_quality_ratio * 100).toFixed(2)}%\n`;
        analysis += `  - Cash as percentage of current assets\n\n`;
      }
    }

    // Summary Statistics
    if (r.summary) {
      analysis += `## 📊 Analysis Summary\n\n`;

      if (r.summary.total_components_calculated) {
        analysis += `**Total Ratios Calculated**: ${r.summary.total_components_calculated}\n\n`;
      }

      if (r.summary.total_ratio_categories) {
        analysis += `**Ratio Categories**: ${r.summary.total_ratio_categories}\n\n`;
      }

      if (r.summary.categories) {
        analysis += `**Breakdown by Category**:\n\n`;
        const cats = r.summary.categories;
        for (const [cat, count] of Object.entries(cats) as [string, number][]) {
          if (count > 0) {
            analysis += `- **${cat.charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, ' ')}**: ${count} ratios\n`;
          }
        }
        analysis += `\n`;
      }

      analysis += `**Status**: ${r.summary.status}\n\n`;
    }

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
      analysis += `## 📋 Financial Health Score\n\n`;
      analysis += `**Overall Score**: ${score}%\n\n`;

      if (scoreNum >= 80) {
        analysis += `✅ **Strong financial position** - Good liquidity and solvency metrics.\n\n`;
      } else if (scoreNum >= 60) {
        analysis += `⚠️ **Moderate financial position** - Some areas for improvement.\n\n`;
      } else {
        analysis += `❌ **Weak financial position** - Concerns about liquidity or leverage.\n\n`;
      }
    }

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
        const analysisText = generateRatioAnalysis(data.response);

        // Extract structured ratio data if available
        let structuredRatios = data.response.ratios || data.response;
        let extractedNumbers = data.response._extracted_numbers || null;

        // If structured data exists, format it properly for table display
        if (structuredRatios && !structuredRatios.liquidity_ratios) {
          // Try to organize flat structure into categories
          structuredRatios = {
            ratios: structuredRatios,
            _extracted_numbers: extractedNumbers
          };
        }

        setMessages([{ text: analysisText, sender: 'bot' }]);
        setComprehensiveBS(data.comprehensive_balance_sheet);
        setRatioData(structuredRatios || data.response);
        setExtractionMethod(data.method || null);
        setResults((prev: any) => ({ ...prev, financial: data.response }));
        setShowResponse(true);
        setDisplayFormat('table');
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
            📊 Comprehensive Financial Ratios Analysis (45+ Ratios)
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
            }}
          >
            {isLoading ? '⏳ Analyzing...' : '📈 Analyze Financial Ratios'}
          </button>
        </div>

        {messages.length > 0 && (
          <div className="text-right mb-4" style={{ paddingRight: '10px', display: 'flex', gap: '8px', justifyContent: 'flex-end', alignItems: 'center', flexWrap: 'wrap' }}>
            {extractionMethod === 'mistral' && (
              <div style={{
                marginRight: 'auto',
                background: '#e0e7ff',
                color: '#4338ca',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 2px 5px rgba(67, 56, 202, 0.1)'
              }}>
                <span style={{ fontSize: '14px' }}>✨</span> High-Precision Mistral OCR
              </div>
            )}
            <button
              onClick={() => setDisplayFormat(displayFormat === 'table' ? 'markdown' : 'table')}
              style={{
                padding: '8px 16px',
                background: displayFormat === 'table' ? '#667eea' : '#764ba2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              {displayFormat === 'table' ? '📊 Table' : '📄 Markdown'}
            </button>
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
              }}
            >
              {activeTab === 'breakdown' ? '📊 Breakdown' : '📈 Analysis'}
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
              }}
            >
              {showResponse ? '👁️ Hide' : '👁️ Show'}
            </button>
          </div>
        )}

        {messages.length > 0 && showResponse && (
          <div className="response">
            {displayFormat === 'table' && ratioData ? (
              <div style={{
                background: '#f8f9fc',
                border: '1px solid #e0e7ff',
                borderRadius: '12px',
                padding: '20px',
                maxHeight: '70vh',
                overflowY: 'auto',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.15)',
              }}>
                <FinancialTableDisplay
                  ratios={ratioData.ratios || ratioData}
                  extractedNumbers={ratioData._extracted_numbers}
                />
              </div>
            ) : (
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
                    <div key={index} className={`message ${msg.sender === 'bot' ? 'bot-message' : ''}`}
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
                  <div style={{
                    background: 'white',
                    borderLeft: '5px solid #667eea',
                    borderRadius: '8px',
                    padding: '16px',
                    marginBottom: '16px',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                  }}>
                    <div className="bot-message-markdown">
                      <ReactMarkdown>{generateBalanceSheetTable(comprehensiveBS)}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {comprehensiveBS && <BalanceSheetVisualization comprehensiveBS={comprehensiveBS} />}
      </div>
    </div>
  );
};

export default FinancialRatio;
