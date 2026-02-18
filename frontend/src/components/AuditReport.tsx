import React, { useState } from 'react';
import { useAnalysis } from '../context/AnalysisContext';

type CAROApplicability = {
  is_applicable: boolean | null;
  available_in_report: boolean | null;
  reason: string;
};

type AuditReportInsights = {
  Qualified_opinion: string;
  Emphasis_of_matter: string;
  CARO_applicability: CAROApplicability;
  CARO_negative_points: { rule: string; remarks: string }[];
  Cautionary_Analysis: string[];
};

const AuditorReport: React.FC<{ recentFileName: string | null }> = ({ recentFileName }) => {
  const [insights, setInsights] = useState<AuditReportInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showResponse, setShowResponse] = useState(true);
  const { setResults } = useAnalysis();

  const fetchMarkdownFileAndAnalyze = async () => {
    if (!recentFileName) {
      setError('No file selected. Please upload a Markdown file first.');
      return;
    }

    const markdownFileName = recentFileName.replace('.pdf', '.md');
    const markdownFilePath = `https://finbizinfo.com/api/saved_markdowns/${encodeURIComponent(markdownFileName)}`;
    const backendUrl = 'https://finbizinfo.com/api/api/analyze-audit-report';

    setLoading(true);
    setError('');
    setInsights(null);

    try {
      const fileResponse = await fetch(markdownFilePath);
      if (!fileResponse.ok) throw new Error(`Failed to fetch the markdown file (${fileResponse.status})`);

      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('md_file', markdownBlob, markdownFileName);

      const response = await fetch(backendUrl, { method: 'POST', body: formData });
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Failed to analyze the report.');

      setInsights(data.insights);
      if (data.insights) {
        const summaryText = insightsToMarkdown(data.insights);
        setResults((prev: any) => ({ ...prev, audit: summaryText }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const renderInsights = (data: AuditReportInsights) => {
    const isCAROApplicable = data.CARO_applicability?.is_applicable === true;

    return (
      <div className="space-y-8 w-full max-h-[70vh] overflow-y-auto pr-2">
        {/* Qualifications */}
        <section className="bg-white rounded-lg shadow p-6 border border-blue-100 w-full">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Qualifications (Reported by Auditor)</h2>
          <p className="text-black-900">{data.Qualified_opinion || 'Not available'}</p>
        </section>

        {/* Emphasis of Matter */}
        <section className="bg-white rounded-lg shadow p-6 border border-blue-100 w-full">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Emphasis of Matter</h2>
          <p className="text-black-900">{data.Emphasis_of_matter || 'Not available'}</p>
        </section>

        {/* CARO Applicability */}
        <section className="bg-white rounded-lg shadow p-6 border border-blue-100 w-full">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">CARO Applicability</h2>
          <ul className="text-black-900 list-none pl-0">
            <li>
              <strong>Applicable:</strong>{' '}
              {data.CARO_applicability?.is_applicable === true
                ? <span className="text-green-800 font-semibold">Yes</span>
                : data.CARO_applicability?.is_applicable === false
                ? <span className="text-red-800 font-semibold">No</span>
                : 'Not available'}
            </li>
            {isCAROApplicable && (
              <li>
                <strong>Available in Report:</strong>{' '}
                {data.CARO_applicability?.available_in_report === true
                  ? <span className="text-green-800 font-semibold">Yes</span>
                  : data.CARO_applicability?.available_in_report === false
                  ? <span className="text-red-800 font-semibold">No</span>
                  : 'Not available'}
              </li>
            )}
            <li>
              <strong>Reason:</strong>{' '}
              {data.CARO_applicability?.reason || 'Not available'}
            </li>
          </ul>
        </section>

        {/* CARO Points with Negative Sentiments */}
        {isCAROApplicable && (
          <section className="bg-white rounded-lg shadow p-6 border border-blue-100 w-full">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">CARO Points with Negative Sentiments (Prequisition)</h2>
            {data.CARO_negative_points && data.CARO_negative_points.length > 0 ? (
              <ul className="list-disc list-inside text-black-900">
                {data.CARO_negative_points.map((rule, idx) => (
                  <li key={idx}><strong>{rule.rule}:</strong> {rule.remarks}</li>
                ))}
              </ul>
            ) : (
              <p className="text-black-900">No negative sentiment points found in CARO remarks.</p>
            )}
          </section>
        )}

        {/* Cautionary Analyses */}
        <section className="bg-white rounded-lg shadow p-6 border border-blue-100 w-full">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Cautionary Analyses (by AI)</h2>
          {data.Cautionary_Analysis && data.Cautionary_Analysis.length > 0 ? (
            <ul className="list-disc list-inside text-black-900">
              {data.Cautionary_Analysis.map((point, idx) => (
                <li key={idx}>{point}</li>
              ))}
            </ul>
          ) : (
            <p className="text-black-900">No cautionary analysis provided.</p>
          )}
        </section>
      </div>
    );
  };

  function insightsToMarkdown(data: AuditReportInsights): string {
    if (!data || typeof data !== 'object') return 'No insights available.';
    let result = '';
    result += `**Qualified Opinion:** ${data.Qualified_opinion || ''}\n\n`;
    result += `**Emphasis of Matter:** ${data.Emphasis_of_matter || ''}\n\n`;
    result += `**CARO Applicability:**\n`;
    result += `- Applicable: ${
      data.CARO_applicability?.is_applicable === true
        ? 'Yes'
        : data.CARO_applicability?.is_applicable === false
        ? 'No'
        : 'Not available'
    }\n`;
    result += `- Available in Report: ${
      data.CARO_applicability?.available_in_report === true
        ? 'Yes'
        : data.CARO_applicability?.available_in_report === false
        ? 'No'
        : 'Not available'
    }\n`;
    result += `- Reason: ${data.CARO_applicability?.reason || 'Not available'}\n\n`;
    result += `**CARO Points with Negative Sentiments:**\n`;
    if (data.CARO_negative_points && data.CARO_negative_points.length > 0) {
      data.CARO_negative_points.forEach((item) => {
        result += `- **${item.rule}:** ${item.remarks}\n`;
      });
    }
    result += `\n**Cautionary Analyses:**\n`;
    if (data.Cautionary_Analysis && data.Cautionary_Analysis.length > 0) {
      data.Cautionary_Analysis.forEach((point) => {
        result += `- ${point}\n`;
      });
    }
    return result.trim();
  }

  return (
    <div className="w-full max-w-screen-lg mx-auto py-8 px-2 sm:px-6">
      <div className="text-center mb-6 w-full">
        {recentFileName && (
          <p className="text-blue-900 mt-2 text-base">
            <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
          </p>
        )}
        <button
          onClick={fetchMarkdownFileAndAnalyze}
          disabled={!recentFileName || loading}
          className={`mt-4 bg-blue-700 hover:bg-blue-800 text-white font-bold py-2 px-6 rounded shadow transition-all duration-150 ${
            (!recentFileName || loading) && 'opacity-50 cursor-not-allowed'
          }`}
        >
          {loading ? (
            <span className="inline-block animate-spin border-4 border-blue-500 border-t-blue-700 rounded-full w-6 h-6 align-middle"></span>
          ) : (
            'Analyze Report'
          )}
        </button>
        {error && (
          <div className="mt-4 text-red-700 bg-red-100 border border-red-300 rounded p-3 max-w-lg mx-auto">
            <span className="font-semibold">Error:</span> {error}
          </div>
        )}
      </div>

      {insights && (
        <div className="text-right mb-2 w-full">
          <button
            onClick={() => setShowResponse((prev) => !prev)}
            className="px-3 py-1 bg-black-300 hover:bg-black-400 rounded text-sm text-black-900"
          >
            {showResponse ? 'Hide Response' : 'Show Response'}
          </button>
        </div>
      )}

      {insights && showResponse && (
        <div id="results-section" className="text-black w-full">
          <div id="results-container" className="w-full">{renderInsights(insights)}</div>
        </div>
      )}
    </div>
  );
};

export default AuditorReport;
