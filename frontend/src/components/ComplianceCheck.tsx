import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';

interface ComplianceCheckProps {
  financialData: any;
  country: string;
}

export default function ComplianceCheck({}: ComplianceCheckProps) {
  const [results, setResults] = React.useState<any[]>([]);

  

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <div
          key={index}
          className={`p-4 rounded-lg ${
            result.status === 'compliant'
              ? 'bg-green-50'
              : result.status === 'warning'
              ? 'bg-yellow-50'
              : 'bg-red-50'
          }`}
        >
          <div className="flex items-start gap-3">
            {result.status === 'compliant' ? (
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
            ) : result.status === 'warning' ? (
              <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            )}
            <div>
              <h3 className="font-medium text-gray-900">
                {result.requirement}
              </h3>
              <p className="mt-1 text-sm text-gray-600">
                {result.details}
              </p>
              {result.recommendations && (
                <p className="mt-2 text-sm text-gray-600">
                  Recommendation: {result.recommendations}
                </p>
              )}
              <p className="mt-2 text-xs text-gray-500">
                {result.act} - Section {result.section}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}