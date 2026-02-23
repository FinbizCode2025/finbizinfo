import React, { useState } from 'react';
import axios from 'axios';
import FinancialInsightsReport from './FinancialInsightsReport';
import Probe42Data from './Probe42Data';

interface ComprehensiveReportProps {
  sessionId: string | null;
}

const ComprehensiveFinancialReport: React.FC<ComprehensiveReportProps> = ({ sessionId }) => {
  const [data, setData] = useState<{
    ratios?: any;
    compliance?: string;
    auditor?: string;
    director?: string;
    summary?: string;
  }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchAllReports = async () => {
    if (!sessionId) {
      setError('Please upload a document first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Fetch all reports in parallel
      const [ratiosRes, complianceRes, auditorRes, directorRes, summaryRes] = await Promise.allSettled([
        axios.post('http://127.0.0.1:5002/chat/financial-ratio', { session_id: sessionId }),
        axios.post('http://127.0.0.1:5002/chat/compliance-gap', { session_id: sessionId }),
        axios.post('http://127.0.0.1:5002/chat/auditor-report', { session_id: sessionId }),
        axios.post('http://127.0.0.1:5002/chat/director-report', { session_id: sessionId }),
        axios.post('http://127.0.0.1:5002/chat/summary', { session_id: sessionId }),
      ]);

      const newData: typeof data = {};

      // Ratios result: support multiple response shapes and capture errors
      if (ratiosRes.status === 'fulfilled') {
        const resp = ratiosRes.value.data;
        // Backend may wrap output in { response: {...} } or return the object directly
        newData.ratios = resp.response || resp;
        console.debug('Financial ratios response:', resp);
      } else {
        // Attempt to pull server error message from rejection
        try {
          const errRes = ratiosRes.reason?.response?.data;
          const msg = errRes?.error || errRes?.message || ratiosRes.reason?.message || 'Failed to fetch ratios';
          setError(`Financial ratios error: ${msg}`);
        } catch (e) {
          setError('Failed to fetch financial ratios.');
        }
      }
      if (complianceRes.status === 'fulfilled') {
        newData.compliance = complianceRes.value.data.response;
      }
      if (auditorRes.status === 'fulfilled') {
        newData.auditor = auditorRes.value.data.response;
      }
      if (directorRes.status === 'fulfilled') {
        newData.director = directorRes.value.data.response;
      }
      if (summaryRes.status === 'fulfilled') {
        newData.summary = summaryRes.value.data.response;
      }

      setData(newData);
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError('Failed to fetch reports. Please try again.');
    }

    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <button
        onClick={fetchAllReports}
        disabled={loading || !sessionId}
        className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-800 text-white font-bold rounded-lg hover:from-blue-700 hover:to-blue-900 transition disabled:opacity-50"
      >
        {loading ? '📊 Generating Comprehensive Report...' : '📊 Generate Comprehensive Financial Report'}
      </button>

      {error && (
        <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {data.ratios && Object.keys(data.ratios).length > 0 && (
        <FinancialInsightsReport
          ratios={data.ratios?.ratios || data.ratios}
          complianceReport={data.compliance}
          auditorReport={data.auditor}
          directorReport={data.director}
          summary={data.summary}
        />
      )}
    </div>
  );
};

export default ComprehensiveFinancialReport;
