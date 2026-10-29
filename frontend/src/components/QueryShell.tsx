import React, { useState } from 'react';
import { Search, Compass, ArrowRight, Sparkles, Loader2, GitCommit, Layers, Clock, AlertCircle } from 'lucide-react';
import { RetrievalMode, EvidenceBundleResponse } from '../types/api';
import { executeRetrieve } from '../services/apiClient';

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
  const [bundle, setBundle] = useState<EvidenceBundleResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await executeRetrieve({
        query: query.trim(),
        mode,
        tenant_id: tenantId,
        corpus_id: corpusId,
        top_k_vector: 5,
        max_depth: 2,
        max_fan_out: 15,
      });
      setBundle(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Retrieval failed');
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
          <h2 className="text-lg font-semibold text-white">Hybrid Retrieval Planner</h2>
        </div>
        <span className="text-xs bg-brand-500/10 text-brand-400 px-2.5 py-1 rounded-full border border-brand-500/20 font-medium">
          Phase 4 Active
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
                setBundle(null);
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
          <label className="text-xs font-medium text-slate-400">Question Input</label>
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

        {/* Mode Selector */}
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
                <span>Retrieving & Fusing Evidence...</span>
              </>
            ) : (
              <>
                <span>Execute Retrieval</span>
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

      {/* Live Evidence Bundle Results */}
      {bundle && (
        <div className="space-y-5 pt-2 border-t border-slate-800">
          {/* Telemetry Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Total Latency</span>
              <p className="text-base font-bold text-white flex items-center gap-1 mt-0.5">
                <Clock className="w-3.5 h-3.5 text-brand-400" />
                {bundle.metrics.latency_total_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Vector Search</span>
              <p className="text-base font-bold text-emerald-400 mt-0.5">
                {bundle.metrics.latency_vector_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Graph Traversal</span>
              <p className="text-base font-bold text-brand-300 mt-0.5">
                {bundle.metrics.latency_graph_ms} ms
              </p>
            </div>
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-3">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Fused Evidence</span>
              <p className="text-base font-bold text-white mt-0.5">
                {bundle.metrics.fused_chunks_count} Chunks
              </p>
            </div>
          </div>

          {/* Graph Traversed Paths */}
          {bundle.graph_paths.length > 0 && (
            <div className="space-y-2.5">
              <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                <GitCommit className="w-3.5 h-3.5 text-brand-400" />
                Traversed Knowledge Graph Path ({bundle.graph_paths.length} Edges)
              </h3>
              <div className="space-y-2">
                {bundle.graph_paths.map((p, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-850 border border-brand-500/30 rounded-xl p-3 flex flex-wrap items-center gap-2 text-xs"
                  >
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                      Hop {p.hop}
                    </span>
                    <span className="font-semibold text-white">{p.source_entity}</span>
                    <span className="text-brand-300 font-mono text-[11px]">--[{p.relation}]--&gt;</span>
                    <span className="font-semibold text-white">{p.target_entity}</span>
                    <span className="text-[10px] text-slate-400 ml-auto font-mono">
                      Confidence: {Math.round(p.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fused Evidence Chunks */}
          <div className="space-y-2.5">
            <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              Fused Evidence Bundle ({bundle.fused_evidence_chunks.length} Deduplicated Passages)
            </h3>
            <div className="space-y-2">
              {bundle.fused_evidence_chunks.map((c) => (
                <div
                  key={c.chunk_id}
                  className="bg-slate-850 border border-slate-750 rounded-xl p-3 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-slate-400">{c.chunk_id.substring(0, 24)}...</span>
                      {c.section_header && (
                        <span className="text-slate-300 bg-slate-800 px-1.5 py-0.2 rounded">
                          {c.section_header}
                        </span>
                      )}
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase ${
                        c.source === 'fused'
                          ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20'
                          : c.source === 'graph'
                          ? 'bg-brand-500/10 text-brand-300 border border-brand-500/20'
                          : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                      }`}
                    >
                      {c.source} (score: {c.similarity_score.toFixed(2)})
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                    {c.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
