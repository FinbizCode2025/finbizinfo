export interface FinancialData {
  year: number;
  currentAssets: number;
  currentLiabilities: number;
  totalAssets: number;
  totalLiabilities: number;
  netIncome: number;
  revenue: number;
  quickAssets: number;
  inventory: number;
  totalEquity: number;
  ebit: number;
  interestExpense: number;
}

export interface FinancialRatios {
  currentRatio: number;
  quickRatio: number;
  debtToEquity: number;
  returnOnAssets: number;
  returnOnEquity: number;
  grossMargin: number;
  operatingMargin: number;
  netMargin: number;
  interestCoverageRatio: number;
}

export interface RatioAnalysis {
  ratio: keyof FinancialRatios;
  value: number;
  benchmark: number;
  status: 'healthy' | 'warning' | 'critical';
  explanation: string;
  recommendation?: string;
}

export interface LLMModel {
  id: string;
  name: string;
  description: string;
}

export interface Country {
  code: string;
  name: string;
  standards: string[];
}

export interface ComplianceCheck {
  standard: string;
  status: 'compliant' | 'non-compliant' | 'partial';
  details: string;
  recommendations?: string;
}