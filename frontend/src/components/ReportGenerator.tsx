import React from 'react';

import PropTypes from 'prop-types';

interface ReportGeneratorProps {
  pdfContent: string | null;
}

export default function ReportGenerator({ pdfContent }: ReportGeneratorProps) {
  console.log('PDF Content in ReportGenerator:', pdfContent); // Debug log
  return (
    <div className="bg-white rounded-lg p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Financial Analysis Report
      </h2>
      {pdfContent ? (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Analysis</h3>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{pdfContent}</p>
        </div>
      ) : (
        <p className="text-sm text-gray-500">No analysis available. Upload a PDF to get started.</p>
      )}
    </div>
  );
}
