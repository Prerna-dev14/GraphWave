import React from 'react';
import { Database, Network, RefreshCw, GitFork } from 'lucide-react';
import { ReadyHealthResponse } from '../types/api';

interface HeaderProps {
  health: ReadyHealthResponse | null;
  loadingHealth: boolean;
  onRefreshHealth: () => void;
  tenantId: string;
  corpusId: string;
  onTenantChange: (val: string) => void;
  onCorpusChange: (val: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  loadingHealth,
  onRefreshHealth,
  tenantId,
  corpusId,
  onTenantChange,
  onCorpusChange,
}) => {
  const pgStatus = health?.dependencies?.postgresql?.status || 'unhealthy';
  const neoStatus = health?.dependencies?.neo4j?.status || 'unhealthy';

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-brand-500/20 text-slate-950">
            <GitFork className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">GraphWeave</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 font-medium">
                Phase 0/1
              </span>
            </div>
            <p className="text-xs text-slate-400">GraphRAG & Cross-Document Provenance Platform</p>
          </div>
        </div>

        {/* Tenant/Corpus & Health Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Tenant Selector */}
          <div className="flex items-center space-x-2 bg-slate-850 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
            <span className="text-slate-400">Tenant:</span>
            <input
              type="text"
              value={tenantId}
              onChange={(e) => onTenantChange(e.target.value)}
              className="bg-transparent text-white font-mono focus:outline-none w-28"
            />
          </div>

          {/* Corpus Selector */}
          <div className="flex items-center space-x-2 bg-slate-850 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
            <span className="text-slate-400">Corpus:</span>
            <input
              type="text"
              value={corpusId}
              onChange={(e) => onCorpusChange(e.target.value)}
              className="bg-transparent text-white font-mono focus:outline-none w-28"
            />
          </div>

          {/* PostgreSQL Badge */}
          <div className="flex items-center space-x-1.5 bg-slate-850 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs" title={health?.dependencies?.postgresql?.details || ''}>
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">Postgres:</span>
            <span
              className={`w-2 h-2 rounded-full ${
                pgStatus === 'healthy' ? 'bg-emerald-400' : pgStatus === 'degraded' ? 'bg-amber-400' : 'bg-rose-400'
              }`}
            />
          </div>

          {/* Neo4j Badge */}
          <div className="flex items-center space-x-1.5 bg-slate-850 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs" title={health?.dependencies?.neo4j?.details || ''}>
            <Network className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">Neo4j:</span>
            <span
              className={`w-2 h-2 rounded-full ${
                neoStatus === 'healthy' ? 'bg-emerald-400' : neoStatus === 'degraded' ? 'bg-amber-400' : 'bg-rose-400'
              }`}
            />
          </div>

          {/* Health Refresh */}
          <button
            onClick={onRefreshHealth}
            disabled={loadingHealth}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            title="Refresh Health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
