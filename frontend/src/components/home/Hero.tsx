import { ChevronRight } from 'lucide-react';

export default function Hero() {
  return (
    <div className="bg-blue-50 border-b border-blue-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-3xl">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Transform Financial Data into Actionable Insights
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            Our AI-powered platform analyzes financial statements to provide deep insights, 
            ratio analysis, and compliance checks. Perfect for CFOs, analysts, and decision-makers 
            who need quick, accurate financial intelligence.
          </p>
          <div className="flex gap-4">
            <div className="flex items-center gap-2 text-blue-600">
              <ChevronRight className="h-5 w-5" />
              <span>Instant Ratio Analysis</span>
            </div>
            <div className="flex items-center gap-2 text-blue-600">
              <ChevronRight className="h-5 w-5" />
              <span>Compliance Verification</span>
            </div>
            <div className="flex items-center gap-2 text-blue-600">
              <ChevronRight className="h-5 w-5" />
              <span>AI-Powered Insights</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}