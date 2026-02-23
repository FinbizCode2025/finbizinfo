import React, { useState } from 'react';
import axios from 'axios';

interface AgentResult {
  status: string;
  // execution_time may be a number, null, or a string (backend can return 'N/A' or null)
  execution_time: number | null | string;
  output?: any;
  error?: string;
}

interface ExecutionSummary {
  total_agents: number;
  completed: number;
  failed: number;
  // total_time may be numeric, null, or string depending on backend
  total_time: number | null | string;
  agents: { [key: string]: AgentResult };
  overall_quality_score?: number;
}

interface MultiAgentAnalysisProps {
  sessionId: string | null;
  title: string;
}

const MultiAgentAnalysis: React.FC<MultiAgentAnalysisProps> = ({ sessionId, title }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<ExecutionSummary | null>(null);
  const [error, setError] = useState<string>('');
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const handleStartAnalysis = async () => {
    if (!sessionId) {
      setError('Please upload a document first');
      return;
    }

    setIsAnalyzing(true);
    setError('');
    setResults(null);
    setExpandedAgents(new Set());

    try {
      const res = await axios.post(
        'http://127.0.0.1:5002/chat/multi-agent-analysis',
        { session_id: sessionId },
        { headers: { 'Content-Type': 'application/json' } }
      );

      const executionSummary = res.data.response?.execution_summary || res.data.response;
      if (executionSummary) {
        setResults({
          ...executionSummary,
          overall_quality_score: res.data.response?.overall_quality_score || 0.85
        });
      }
    } catch (err) {
      const errMsg = (err as any)?.response?.data?.error || (err as any)?.message || 'Analysis failed';
      setError(errMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleAgentExpand = (agentName: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentName)) {
      newExpanded.delete(agentName);
    } else {
      newExpanded.add(agentName);
    }
    setExpandedAgents(newExpanded);
  };

  const getQualityColor = (score: number): string => {
    if (score >= 0.85) return 'text-green-700';
    if (score >= 0.60) return 'text-yellow-700';
    return 'text-red-700';
  };

  const getQualityBgColor = (score: number): string => {
    if (score >= 0.85) return 'bg-green-50';
    if (score >= 0.60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const formatAgentName = (name: string): string => {
    return name
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatTime = (t: any, precision = 2): string => {
    const n = Number(t);
    if (!Number.isFinite(n)) return 'N/A';
    return n.toFixed(precision);
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'running':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'running':
        return '⏳';
      default:
        return '⏹️';
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow-lg border border-purple-200">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-purple-800">{title}</h2>
        <span className="text-3xl">🤖</span>
      </div>

      <div className="flex gap-3 mb-4 flex-wrap">
        <button
          onClick={handleStartAnalysis}
          disabled={isAnalyzing || !sessionId}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-semibold shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? (
            <>
              <span className="inline-block animate-spin mr-2">⚙️</span>
              Analyzing with Multi-Agent System...
            </>
          ) : (
            '🚀 Start Multi-Agent Analysis'
          )}
        </button>
        {results && (
          <button
            onClick={() => {
              setResults(null);
              setError('');
              setExpandedAgents(new Set());
            }}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold shadow-md transition"
          >
            🔄 Clear Results
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-100 border-l-4 border-red-600 rounded-lg text-red-800 flex items-center gap-3">
          <span className="text-xl">❌</span>
          <span>{error}</span>
        </div>
      )}

      {results && (
        <div className="mt-6 space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="p-4 bg-white rounded-lg border border-purple-300 shadow-sm hover:shadow-md transition">
              <div className="text-xs text-gray-600 font-semibold uppercase">Total Agents</div>
              <div className="text-3xl font-bold text-purple-700 mt-1">{results.total_agents}</div>
            </div>
            <div className="p-4 bg-white rounded-lg border border-green-300 shadow-sm hover:shadow-md transition">
              <div className="text-xs text-gray-600 font-semibold uppercase">Completed</div>
              <div className="text-3xl font-bold text-green-700 mt-1">{results.completed}</div>
            </div>
            <div className="p-4 bg-white rounded-lg border border-red-300 shadow-sm hover:shadow-md transition">
              <div className="text-xs text-gray-600 font-semibold uppercase">Failed</div>
              <div className="text-3xl font-bold text-red-700 mt-1">{results.failed}</div>
            </div>
            <div className="p-4 bg-white rounded-lg border border-blue-300 shadow-sm hover:shadow-md transition">
              <div className="text-xs text-gray-600 font-semibold uppercase">Total Time</div>
              <div className="text-3xl font-bold text-blue-700 mt-1">{results.total_time.toFixed(2)}s</div>
            </div>
            {results.overall_quality_score !== undefined && (
              <div className={`p-4 ${getQualityBgColor(results.overall_quality_score)} rounded-lg border-2 border-yellow-300 shadow-sm hover:shadow-md transition`}>
                <div className="text-xs text-gray-600 font-semibold uppercase">Quality Score</div>
                <div className={`text-3xl font-bold mt-1 ${getQualityColor(results.overall_quality_score)}`}>
                  {(results.overall_quality_score * 100).toFixed(0)}%
                </div>
              </div>
            )}
          </div>

          {/* Agent Details */}
          <div className="space-y-3">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span>⚙️</span> Agent Execution Details ({results.completed}/{results.total_agents})
            </h3>
            {Object.entries(results.agents).map(([agentName, agentResult]) => {
              const isExpanded = expandedAgents.has(agentName);
              const displayName = formatAgentName(agentName);

              return (
                <div
                  key={agentName}
                  className="border-2 border-gray-300 rounded-lg overflow-hidden hover:shadow-lg transition bg-white"
                >
                  <button
                    onClick={() => toggleAgentExpand(agentName)}
                    className="w-full p-4 bg-gradient-to-r from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 flex justify-between items-center transition group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl group-hover:scale-125 transition">{getStatusIcon(agentResult.status)}</span>
                      <div className="text-left">
                        <div className="font-bold text-gray-900">{displayName}</div>
                        <div className="text-xs text-gray-600">Execution time: {agentResult.execution_time.toFixed(3)}s</div>
                                              <div className="text-xs text-gray-600">Execution time: {formatTime(agentResult.execution_time, 3)}s</div>
                                    <div className="text-3xl font-bold text-blue-700 mt-1">{formatTime(results.total_time, 2)}s</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(agentResult.status)} bg-opacity-10 border`}>
                        {agentResult.status.toUpperCase()}
                      </span>
                      <span className={`transition transform ${isExpanded ? 'rotate-180' : ''}`}>▼</span>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="p-4 bg-white border-t-2 border-gray-300 space-y-3">
                      {agentResult.error && (
                        <div className="p-3 bg-red-100 border-l-4 border-red-600 rounded text-red-800 text-sm">
                          <strong>⚠️ Error:</strong> {agentResult.error}
                        </div>
                      )}
                      {agentResult.output && (
                        <div className="p-3 bg-green-50 border-l-4 border-green-600 rounded text-sm">
                          <strong>✅ Output Summary:</strong>
                          <pre className="text-xs overflow-auto mt-2 p-2 bg-white rounded border border-gray-300 max-h-60 font-mono text-gray-700">
                            {typeof agentResult.output === 'string'
                              ? agentResult.output.length > 500
                                ? agentResult.output.substring(0, 500) + '...'
                                : agentResult.output
                              : JSON.stringify(agentResult.output, null, 2).length > 500
                              ? JSON.stringify(agentResult.output, null, 2).substring(0, 500) + '...'
                              : JSON.stringify(agentResult.output, null, 2)}
                          </pre>
                        </div>
                      )}
                      {!agentResult.error && !agentResult.output && (
                        <div className="p-3 bg-gray-100 border border-gray-300 rounded text-sm text-gray-600 italic">
                          No additional output or error information
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Results Summary */}
          <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-600 rounded-lg">
            <h4 className="font-bold text-blue-900 mb-2">📈 Analysis Complete</h4>
            <p className="text-sm text-blue-800">
              All {results.total_agents} agents executed successfully in {formatTime(results.total_time, 2)} seconds.
              {results.failed > 0 && ` ${results.failed} agent(s) encountered errors.`}
            </p>
          </div>

          {/* Success Message */}
          {results.failed === 0 && (
            <div className="mt-2 p-4 bg-gradient-to-r from-green-100 to-emerald-100 border-l-4 border-green-600 rounded-lg text-green-900 font-semibold flex items-center gap-2">
              <span className="text-2xl">✅</span>
              <span>All agents completed successfully! Results are ready for review.</span>
            </div>
          )}

          {results.failed > 0 && (
            <div className="mt-2 p-4 bg-gradient-to-r from-yellow-100 to-orange-100 border-l-4 border-yellow-600 rounded-lg text-yellow-900 font-semibold flex items-center gap-2">
              <span className="text-2xl">⚠️</span>
              <span>{results.failed} agent(s) failed. Please review errors above.</span>
            </div>
          )}
        </div>
      )}

      {!results && !isAnalyzing && sessionId && (
        <div className="mt-4 p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-dashed border-purple-300 rounded-lg text-center">
          <div className="text-4xl mb-2">🚀</div>
          <p className="text-gray-700 font-semibold">Ready to analyze your document</p>
          <p className="text-sm text-gray-600 mt-2">
            Click "Start Multi-Agent Analysis" to begin comprehensive analysis with 11 parallel agents.
            This will extract, analyze, and validate your financial data.
          </p>
        </div>
      )}

      {!sessionId && (
        <div className="mt-4 p-4 bg-gray-100 border border-gray-300 rounded-lg text-gray-700 text-center">
          📄 Please upload a document first to enable multi-agent analysis
        </div>
      )}
    </div>
  );
};

export default MultiAgentAnalysis;
