import React, { useState } from 'react';
import { Search, Compass, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';

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

export const QueryShell: React.FC = () => {
  const [query, setQuery] = useState(BENCHMARK_QUERIES[0].q);
  const [mode, setMode] = useState<'hybrid' | 'vector' | 'graph'>('hybrid');
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSubmittedQuery(query.trim());
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Compass className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Multi-Hop Query Explorer</h2>
        </div>
        <span className="text-xs bg-brand-500/10 text-brand-400 px-2.5 py-1 rounded-full border border-brand-500/20 font-medium">
          Retrieval Planner Shell (Phase 0/1 Ready)
        </span>
      </div>

      {/* Preset Questions */}
      <div>
        <label className="text-xs font-medium text-slate-400 flex items-center gap-1.5 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-brand-400" />
          Test Benchmark Questions:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {BENCHMARK_QUERIES.map((bq) => (
            <button
              key={bq.q}
              type="button"
              onClick={() => {
                setQuery(bq.q);
                setSubmittedQuery(null);
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
            className="px-5 py-2 rounded-xl text-xs font-semibold text-slate-950 bg-brand-400 hover:bg-brand-300 transition-colors flex items-center space-x-1.5 shadow-md shadow-brand-500/20"
          >
            <span>Preview Planner Flow</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      {/* Query Preview / Roadmap State */}
      {submittedQuery && (
        <div className="border border-brand-500/30 bg-slate-850/80 rounded-xl p-4 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-brand-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Query Planner Configured: {mode.toUpperCase()}</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Max Depth: 2 | Fan-Out: 15</span>
          </div>

          <div className="text-xs text-slate-300 bg-slate-900/90 rounded-lg p-3 border border-slate-800 space-y-1 font-mono">
            <p className="text-slate-400">Target Question: <span className="text-white">"{submittedQuery}"</span></p>
            <p className="text-slate-400">Seed Vector Retrieval: <span className="text-emerald-400">Pending Phase 4</span></p>
            <p className="text-slate-400">Bounded Cypher Traversal: <span className="text-emerald-400">Pending Phase 4</span></p>
            <p className="text-slate-400">Citation Synthesis & Graph Visualizer: <span className="text-emerald-400">Pending Phase 5</span></p>
          </div>
        </div>
      )}
    </div>
  );
};
