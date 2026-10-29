import React, { useState } from 'react';
import {
  Search,
  Compass,
  ArrowRight,
  Sparkles,
  Loader2,
  GitCommit,
  Clock,
  AlertCircle,
  FileText,
  Bookmark,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';
import { RetrievalMode, QueryResponse, Citation } from '../types/api';
import { executeQuery } from '../services/apiClient';

const BENCHMARK_QUERIES = [
  {
    q: 'Which parent corporation currently owns the OmniMesh distributed cache engine?',
    hops: '2-Hop Cross-Doc',
    docs: 'Acme Cloud -> DataWeaver',
  },
  {
    q: "What cryptographic security standard does ShieldPay's encryption-at-rest provider comply with?",
    hops: '2-Hop Cross-Doc',
    docs: 'ShieldPay -> KryptonVault',
  },
  {
    q: 'Which startup company was founded by the leader of the project that produced the HyperGraph Routing Algorithm?',
    hops: '3-Hop Cross-Doc',
    docs: 'NovaGen -> Synapse -> Apex Neural',
  },
  {
    q: 'Who founded QuantaCore Systems and in what year was their quantum processor released?',
    hops: 'Negative Test',
    docs: 'Missing Evidence (Refusal Required)',
  },
];

interface QueryShellProps {
  tenantId: string;
  corpusId: string;
}

export const QueryShell: React.FC<QueryShellProps> = ({ tenantId, corpusId }) => {
  const [query, setQuery] = useState(BENCHMARK_QUERIES[0].q);
  const [mode, setMode] = useState<RetrievalMode>('hybrid');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSelectedCitation(null);
    try {
      const res = await executeQuery({
        query: query.trim(),
        mode,
        tenant_id: tenantId,
        corpus_id: corpusId,
        max_depth: 2,
        max_fan_out: 15,
      });
      setResult(res);
      if (res.citations.length > 0) {
        setSelectedCitation(res.citations[0]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Query execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Compass className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Multi-Hop Query & Answer Synthesis</h2>
        </div>
        <span className="text-xs bg-brand-500/10 text-brand-400 px-2.5 py-1 rounded-full border border-brand-500/20 font-medium flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" />
          Citation-Grounded Phase 5
        </span>
      </div>

      {/* Preset Questions */}
      <div>
        <label className="text-xs font-medium text-slate-400 flex items-center gap-1.5 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-brand-400" />
          Select Benchmark Question:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {BENCHMARK_QUERIES.map((bq) => (
            <button
              key={bq.q}
              type="button"
              onClick={() => {
                setQuery(bq.q);
                setResult(null);
                setSelectedCitation(null);
              }}
              className={`text-left p-3 rounded-xl border text-xs transition-all ${
                query === bq.q
                  ? 'border-brand-500 bg-brand-500/10 text-brand-200'
                  : 'border-slate-800 bg-slate-850 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-brand-400 border border-slate-700">
                  {bq.hops}
                </span>
                <span className="text-[10px] text-slate-500 truncate">{bq.docs}</span>
              </div>
              <p className="line-clamp-2 leading-relaxed">{bq.q}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-400">Natural Language Question</label>
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a multi-hop question across ingested documents..."
              className="w-full bg-slate-850 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          </div>
        </div>

        {/* Mode Selector & Action */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center space-x-2 bg-slate-850 border border-slate-800 p-1 rounded-xl text-xs">
            <button
              type="button"
              onClick={() => setMode('hybrid')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                mode === 'hybrid'
                  ? 'bg-brand-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Hybrid (Vector + Graph)
            </button>
            <button
              type="button"
              onClick={() => setMode('vector')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                mode === 'vector'
                  ? 'bg-brand-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Vector-Only Baseline
            </button>
            <button
              type="button"
              onClick={() => setMode('graph')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                mode === 'graph'
                  ? 'bg-brand-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Graph-Only Baseline
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-slate-950 bg-gradient-to-r from-brand-400 to-emerald-400 hover:opacity-95 transition-opacity disabled:opacity-50 flex items-center space-x-1.5 shadow-lg shadow-brand-500/10"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Executing GraphRAG Pipeline...</span>
              </>
            ) : (
              <>
                <span>Synthesize Grounded Answer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="flex items-center space-x-2 text-rose-400 text-xs bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Synthesized Answer & Telemetry Result Card */}
      {result && (
        <div className="space-y-6 pt-2 border-t border-slate-800">
          {/* Telemetry Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Total Latency</span>
              <p className="text-sm font-bold text-white flex items-center gap-1 mt-0.5">
                <Clock className="w-3 h-3 text-brand-400" />
                {result.metrics.latency_total_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Vector Search</span>
              <p className="text-sm font-bold text-emerald-400 mt-0.5">
                {result.metrics.latency_vector_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Graph Expansion</span>
              <p className="text-sm font-bold text-brand-300 mt-0.5">
                {result.metrics.latency_graph_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Synthesis</span>
              <p className="text-sm font-bold text-indigo-400 mt-0.5">
                {result.metrics.latency_generation_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Trace ID</span>
              <p className="text-xs font-mono text-slate-300 mt-0.5 truncate" title={result.trace_id}>
                {result.trace_id}
              </p>
            </div>
          </div>

          {/* Synthesized Answer Box */}
          <div className="bg-slate-850 border border-brand-500/40 rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white">Grounded Answer</h3>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                {result.citations.length} Citations Backed
              </span>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {result.answer}
            </p>

            {/* Citations Pill Bar */}
            {result.citations.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <span className="text-xs text-slate-400 font-medium">Verified Source Provenance Citations:</span>
                <div className="flex flex-wrap gap-2">
                  {result.citations.map((c, idx) => (
                    <button
                      key={c.chunk_id}
                      onClick={() => setSelectedCitation(c)}
                      className={`text-xs px-2.5 py-1 rounded-lg border font-mono transition-all flex items-center space-x-1.5 ${
                        selectedCitation?.chunk_id === c.chunk_id
                          ? 'border-brand-500 bg-brand-500/20 text-brand-300 shadow-sm'
                          : 'border-slate-750 bg-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <FileText className="w-3 h-3 text-brand-400" />
                      <span>[{idx + 1}] {c.chunk_id.substring(0, 18)}...</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Interactive Citation Detail Inspector */}
          {selectedCitation && (
            <div className="bg-slate-900 border border-slate-750 rounded-xl p-4 space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-white">Cited Source Chunk Passage</span>
                  {selectedCitation.section_header && (
                    <span className="text-slate-400 bg-slate-800 px-2 py-0.5 rounded text-[11px] flex items-center gap-1">
                      <Bookmark className="w-3 h-3 text-brand-400" />
                      {selectedCitation.section_header}
                    </span>
                  )}
                </div>
                <span className="font-mono text-[11px] text-slate-400">
                  Doc ID: {selectedCitation.document_id.substring(0, 16)}...
                </span>
              </div>
              <p className="text-xs text-slate-300 font-mono bg-slate-850 p-3 rounded-lg border border-slate-800 leading-relaxed whitespace-pre-wrap">
                {selectedCitation.snippet}
              </p>
            </div>
          )}

          {/* Interactive Traversed Graph Paths */}
          {result.graph_paths.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <GitCommit className="w-4 h-4 text-brand-400" />
                  Traversed Knowledge Graph Path (Cross-Document Evidence)
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">
                  Bounded Expansion: Depth 2 | Fan-Out 15
                </span>
              </div>

              <div className="space-y-2">
                {result.graph_paths.map((p, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-850 border border-slate-750/80 rounded-xl p-3.5 flex flex-wrap items-center gap-3 text-xs"
                  >
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                      Hop {p.hop}
                    </span>
                    <div className="px-2.5 py-1 rounded-lg bg-slate-800 text-white font-medium border border-slate-700">
                      {p.source_entity}
                    </div>
                    <div className="flex items-center space-x-1 font-mono text-[11px] text-brand-300 bg-brand-500/10 px-2 py-0.5 rounded-full border border-brand-500/20">
                      <span>--[{p.relation}]--&gt;</span>
                      <span className="text-emerald-400 font-semibold">{Math.round(p.confidence * 100)}%</span>
                    </div>
                    <div className="px-2.5 py-1 rounded-lg bg-slate-800 text-white font-medium border border-slate-700">
                      {p.target_entity}
                    </div>
                    <span className="ml-auto text-[11px] font-mono text-slate-500">
                      Anchored Chunks: {p.source_chunk_ids.join(', ').substring(0, 24)}...
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
