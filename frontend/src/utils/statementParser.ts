import * as XLSX from 'exceljs';
import { FinancialData } from '../types';

interface ParsedFinancialStatement {
  companyName: string;
  statementType: 'balance_sheet' | 'income_statement' | 'cash_flow';
  fiscalYear: number;
  fiscalPeriod: string;
  parsedData: FinancialData;
}

export async function parseFinancialStatement(file: File): Promise<ParsedFinancialStatement> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = new XLSX.Workbook();
        await workbook.xlsx.load(data);

        // Get the first sheet
        const worksheet = workbook.getWorksheet(1); // Access the first worksheet by index
        if (!worksheet) {
          throw new Error('Worksheet not found');
        }
        const jsonData: any[] = [];
        worksheet.eachRow((row, rowNumber) => {
          const rowData: any = {};
          row.eachCell((cell, colNumber) => {
            rowData[`Column${colNumber}`] = cell.value;
          });
          jsonData.push(rowData);
        });

        // Extract company info and statement type from filename or content
        const companyInfo = extractCompanyInfo(file.name, jsonData);
        
        // Parse the financial data based on statement type
        const parsedData = parseStatementData(jsonData, companyInfo.statementType);

        resolve({
          companyName: companyInfo.companyName,
          statementType: companyInfo.statementType,
          fiscalYear: companyInfo.fiscalYear,
          fiscalPeriod: companyInfo.fiscalPeriod,
          parsedData
        });
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsArrayBuffer(file);
  });
}

function extractCompanyInfo(filename: string, data: any[]): {
  companyName: string;
  statementType: 'balance_sheet' | 'income_statement' | 'cash_flow';
  fiscalYear: number;
  fiscalPeriod: string;
} {
  // Implement logic to extract company info from filename or content
  // This is a simplified example
  const statementTypes = {
    'bs': 'balance_sheet',
    'is': 'income_statement',
    'cf': 'cash_flow'
  } as const;

  const filenameParts = filename.toLowerCase().split('_');
  const companyName = filenameParts[0];
  const statementType = statementTypes[filenameParts[1] as keyof typeof statementTypes] || 'balance_sheet';
  
  // Extract year and period from data or filename
  const currentYear = new Date().getFullYear();
  const fiscalYear = parseInt(filenameParts[2]) || currentYear;
  const fiscalPeriod = filenameParts[3]?.replace('.xlsx', '') || 'FY';

  return {
    companyName,
    statementType,
    fiscalYear,
    fiscalPeriod
  };
}

function parseStatementData(jsonData: any[], statementType: string): FinancialData {
  // Initialize financial data object
  const financialData: FinancialData = {
    year: 0,
    currentAssets: 0,
    currentLiabilities: 0,
    totalAssets: 0,
    totalLiabilities: 0,
    netIncome: 0,
    revenue: 0,
    quickAssets: 0,
    inventory: 0,
    totalEquity: 0,
    ebit: 0,
    interestExpense: 0
  };

  // Map common financial statement line items to standardized fields
  const mappings = {
    'balance_sheet': {
      'Current Assets': 'currentAssets',
      'Current Liabilities': 'currentLiabilities',
      'Total Assets': 'totalAssets',
      'Total Liabilities': 'totalLiabilities',
      'Total Equity': 'totalEquity',
      'Inventory': 'inventory',
      'Quick Assets': 'quickAssets'
    },
    'income_statement': {
      'Revenue': 'revenue',
      'Net Income': 'netIncome',
      'EBIT': 'ebit',
      'Interest Expense': 'interestExpense'
    }
  };

  // Parse the data based on statement type
  jsonData.forEach(row => {
    const mapping = mappings[statementType as keyof typeof mappings];
    if (!mapping) return;

    Object.entries(mapping).forEach(([key, field]) => {
      if (row[key]) {
        financialData[field as keyof FinancialData] = parseFloat(row[key]);
      }
    });
  });

  return financialData;
}