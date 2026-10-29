import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Play,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Award,
  Zap,
  Target,
  DollarSign,
  ChevronDown,
  ChevronUp,
  Clock,
  Sparkles,
  Sliders,
} from 'lucide-react';
import {
  EvaluationComparisonResponse,
  EvaluationRunResponse,
  TestCaseResult,
} from '../types/api';
import { fetchEvaluationComparison, triggerEvaluationRun } from '../services/apiClient';

interface EvaluationDashboardProps {
  tenantId: string;
  corpusId: string;
}

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({
  tenantId,
  corpusId,
}) => {
  const [comparison, setComparison] = useState<EvaluationComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxFanOut, setMaxFanOut] = useState(15);
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null);
  const [activeTabMode, setActiveTabMode] = useState<'hybrid' | 'vector' | 'graph'>('hybrid');
  const [error, setError] = useState<string | null>(null);

  const loadBenchmark = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvaluationComparison(tenantId, corpusId, maxDepth, maxFanOut);
      setComparison(data);
    } catch (err: any) {
      console.error('Failed to load comparison benchmark:', err);
      setError(err?.message || 'Failed to execute comparative evaluation benchmark.');
    } finally {
      setLoading(false);
    }
  }, [tenantId, corpusId, maxDepth, maxFanOut]);

  // Load benchmark comparison once on mount
  useEffect(() => {
    loadBenchmark();
  }, [loadBenchmark]);

  const handleRunFreshBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await triggerEvaluationRun({
        tenant_id: tenantId,
        corpus_id: corpusId,
        max_depth: maxDepth,
        max_fan_out: maxFanOut,
      });
      if ('runs' in res) {
        setComparison(res);
      } else {
        await loadBenchmark();
      }
    } catch (err: any) {
      setError(err?.message || 'Benchmark run failed.');
    } finally {
      setLoading(false);
    }
  };

  const getRunByMode = (mode: string): EvaluationRunResponse | undefined => {
    return comparison?.runs?.find((r) => r.retrieval_mode === mode);
  };

  const hybridRun = getRunByMode('hybrid');
  const vectorRun = getRunByMode('vector');
  const graphRun = getRunByMode('graph');

  const activeRun = getRunByMode(activeTabMode);

  return (
    <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">Phase 6: Multi-Hop Evaluation & Tuning Harness</h2>
                <span className="text-[11px] bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded font-mono">
                  Benchmark v1.0.0
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Empirical side-by-side comparison of Vector-Only, Graph-Only, and Hybrid GraphRAG across multi-hop reasoning questions.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Depth / Fan-out tuning */}
          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 font-medium">Depth:</span>
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className="bg-transparent text-white font-mono focus:outline-none cursor-pointer"
            >
              <option value={1} className="bg-slate-900">1 Hop</option>
              <option value={2} className="bg-slate-900">2 Hops</option>
              <option value={3} className="bg-slate-900">3 Hops</option>
            </select>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400 font-medium">Fan-out:</span>
            <select
              value={maxFanOut}
              onChange={(e) => setMaxFanOut(Number(e.target.value))}
              className="bg-transparent text-white font-mono focus:outline-none cursor-pointer"
            >
              <option value={5} className="bg-slate-900">5</option>
              <option value={15} className="bg-slate-900">15</option>
              <option value={30} className="bg-slate-900">30</option>
            </select>
          </div>

          <button
            onClick={handleRunFreshBenchmark}
            disabled={loading}
            className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium px-4 py-2 rounded-xl text-xs shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Running Benchmark...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run 3-Mode Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparative Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Hybrid GraphRAG (Recommended) */}
        <div className="bg-gradient-to-b from-brand-950/40 via-slate-950 to-slate-950 border-2 border-brand-500/50 rounded-2xl p-5 relative overflow-hidden shadow-lg">
          <div className="absolute top-0 right-0 bg-brand-500 text-slate-950 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-bl-xl flex items-center space-x-1">
            <Award className="w-3 h-3" />
            <span>Recommended</span>
          </div>

          <div className="flex items-center space-x-2 mb-3">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <h3 className="text-sm font-bold text-white">Hybrid GraphRAG</h3>
          </div>
          <p className="text-[11px] text-slate-400 mb-4">
            Vector semantic seed discovery combined with bounded Cypher neighborhood expansion.
          </p>

          <div className="space-y-3 pt-2 border-t border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-brand-400" />
                Evidence Recall
              </span>
              <span className="font-mono font-bold text-emerald-400 text-sm">
                {hybridRun ? `${(hybridRun.evidence_recall * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" />
                Answer Correctness
              </span>
              <span className="font-mono font-bold text-emerald-400 text-sm">
                {hybridRun ? `${(hybridRun.answer_correctness * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Latency (p50 / p95)
              </span>
              <span className="font-mono text-slate-200">
                {hybridRun ? `${hybridRun.latency_p50_ms}ms / ${hybridRun.latency_p95_ms}ms` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                Cost / 1k Queries
              </span>
              <span className="font-mono text-slate-200">
                {hybridRun ? `$${(hybridRun.token_cost_usd * 200).toFixed(3)}` : '---'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 2: Vector-Only Baseline */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 mb-3">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">Vector-Only Baseline</h3>
          </div>
          <p className="text-[11px] text-slate-400 mb-4">
            Dense embeddings only. Exhibits severe recall drop on multi-hop disconnected documents.
          </p>

          <div className="space-y-3 pt-2 border-t border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-amber-400" />
                Evidence Recall
              </span>
              <span className="font-mono font-bold text-amber-400 text-sm">
                {vectorRun ? `${(vectorRun.evidence_recall * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                Answer Correctness
              </span>
              <span className="font-mono font-bold text-amber-400 text-sm">
                {vectorRun ? `${(vectorRun.answer_correctness * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Latency (p50 / p95)
              </span>
              <span className="font-mono text-slate-200">
                {vectorRun ? `${vectorRun.latency_p50_ms}ms / ${vectorRun.latency_p95_ms}ms` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                Cost / 1k Queries
              </span>
              <span className="font-mono text-slate-200">
                {vectorRun ? `$${(vectorRun.token_cost_usd * 200).toFixed(3)}` : '---'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: Graph-Only Baseline */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 mb-3">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Graph-Only Baseline</h3>
          </div>
          <p className="text-[11px] text-slate-400 mb-4">
            Structured Cypher traversal only. Finds entity topology but lacks unstructured passage context.
          </p>

          <div className="space-y-3 pt-2 border-t border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-cyan-400" />
                Evidence Recall
              </span>
              <span className="font-mono font-bold text-cyan-400 text-sm">
                {graphRun ? `${(graphRun.evidence_recall * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                Answer Correctness
              </span>
              <span className="font-mono font-bold text-cyan-400 text-sm">
                {graphRun ? `${(graphRun.answer_correctness * 100).toFixed(0)}%` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Latency (p50 / p95)
              </span>
              <span className="font-mono text-slate-200">
                {graphRun ? `${graphRun.latency_p50_ms}ms / ${graphRun.latency_p95_ms}ms` : '---'}
              </span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                Cost / 1k Queries
              </span>
              <span className="font-mono text-slate-200">
                {graphRun ? `$${(graphRun.token_cost_usd * 200).toFixed(3)}` : '---'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Benchmark Analysis Callout */}
      {comparison?.analysis_summary && (
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed font-mono">
          <div className="text-[11px] font-bold text-purple-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Benchmark Empirical Synthesis</span>
          </div>
          <p className="whitespace-pre-line text-slate-400">{comparison.analysis_summary}</p>
        </div>
      )}

      {/* Mode Filter Tabs for Test Cases */}
      <div className="pt-2">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Benchmark Test Case Breakdown ({activeRun?.total_questions || 5} Questions)
          </h3>
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {(['hybrid', 'vector', 'graph'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setActiveTabMode(m)}
                className={`px-3 py-1 rounded-md capitalize transition font-medium ${
                  activeTabMode === m
                    ? 'bg-brand-500 text-slate-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {m === 'vector' ? 'Vector Only' : m === 'graph' ? 'Graph Only' : 'Hybrid GraphRAG'}
              </button>
            ))}
          </div>
        </div>

        {/* Table of Test Cases */}
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Test Case / Category</th>
                  <th className="py-3 px-4">Hops</th>
                  <th className="py-3 px-4">Recall</th>
                  <th className="py-3 px-4">Correctness</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {activeRun?.metrics_detail?.map((tc: TestCaseResult) => {
                  const isExpanded = expandedCaseId === tc.test_case_id;
                  return (
                    <React.Fragment key={tc.test_case_id}>
                      <tr
                        onClick={() => setExpandedCaseId(isExpanded ? null : tc.test_case_id)}
                        className="hover:bg-slate-900/60 cursor-pointer transition"
                      >
                        <td className="py-3 px-4 font-medium text-white">
                          <div className="font-semibold">{tc.test_case_id}: {tc.category}</div>
                          <div className="text-[11px] text-slate-400 truncate max-w-md mt-0.5">
                            {tc.question}
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          {tc.hops === 0 ? '0 (Neg)' : `${tc.hops} Hops`}
                        </td>
                        <td className="py-3 px-4 font-mono">
                          <span
                            className={
                              tc.evidence_recall >= 0.8
                                ? 'text-emerald-400'
                                : tc.evidence_recall >= 0.5
                                ? 'text-amber-400'
                                : 'text-rose-400'
                            }
                          >
                            {(tc.evidence_recall * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono">
                          <span
                            className={
                              tc.answer_correctness >= 0.8
                                ? 'text-emerald-400'
                                : tc.answer_correctness >= 0.5
                                ? 'text-amber-400'
                                : 'text-rose-400'
                            }
                          >
                            {(tc.answer_correctness * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400">
                          {tc.latency_ms}ms
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                              tc.passed
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {tc.passed ? 'PASS' : 'FAIL'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button className="text-slate-400 hover:text-white">
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded View */}
                      {isExpanded && (
                        <tr className="bg-slate-900/40">
                          <td colSpan={7} className="p-4 space-y-3 border-t border-slate-800">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                                <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Generated Answer:</div>
                                <p className="text-slate-200 leading-relaxed font-sans">{tc.generated_answer}</p>
                              </div>
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                                <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Expected Ground Truth:</div>
                                <p className="text-slate-300 leading-relaxed font-sans">{tc.expected_answer}</p>
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-4 text-[11px] font-mono text-slate-400">
                              <span>Retrieved Chunks: <strong className="text-white">{tc.retrieved_chunks_count}</strong></span>
                              <span>Traversed Paths: <strong className="text-white">{tc.traversed_paths_count}</strong></span>
                              <span>Citation Precision: <strong className="text-emerald-400">{(tc.citation_precision * 100).toFixed(0)}%</strong></span>
                              <span>Token Cost: <strong className="text-slate-200">${tc.token_cost_usd}</strong></span>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
};
