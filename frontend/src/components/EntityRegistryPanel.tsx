import React, { useState, useEffect, useCallback } from 'react';
import { Network, Tag, Check, X, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { CanonicalEntityResponse, AmbiguousMatch } from '../types/api';
import { listCanonicalEntities, listAmbiguities, resolveAmbiguity } from '../services/apiClient';

interface EntityRegistryPanelProps {
  tenantId: string;
  corpusId: string;
}

export const EntityRegistryPanel: React.FC<EntityRegistryPanelProps> = ({
  tenantId,
  corpusId,
}) => {
  const [activeTab, setActiveTab] = useState<'entities' | 'ambiguities'>('entities');
  const [entities, setEntities] = useState<CanonicalEntityResponse[]>([]);
  const [ambiguities, setAmbiguities] = useState<AmbiguousMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [fetchedEntities, fetchedAmbiguities] = await Promise.all([
        listCanonicalEntities(tenantId, corpusId).catch(() => []),
        listAmbiguities().catch(() => []),
      ]);
      setEntities(fetchedEntities);
      setAmbiguities(fetchedAmbiguities);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [tenantId, corpusId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleResolve = async (matchId: string, action: 'APPROVE_MERGE' | 'REJECT_MERGE') => {
    setResolvingId(matchId);
    try {
      await resolveAmbiguity(matchId, action);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-brand-400" />
          <h2 className="text-lg font-semibold text-white">Knowledge Graph Entities & Aliases</h2>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          title="Refresh Entities"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 flex space-x-4">
        <button
          onClick={() => setActiveTab('entities')}
          className={`py-2 text-xs font-semibold border-b-2 transition-all flex items-center space-x-1.5 ${
            activeTab === 'entities'
              ? 'border-brand-500 text-brand-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Tag className="w-3.5 h-3.5" />
          <span>Canonical Entities</span>
          <span className="bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded-full text-[10px]">
            {entities.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('ambiguities')}
          className={`py-2 text-xs font-semibold border-b-2 transition-all flex items-center space-x-1.5 ${
            activeTab === 'ambiguities'
              ? 'border-brand-500 text-brand-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          <span>Ambiguity Review Queue</span>
          <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
            ambiguities.length > 0 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-400'
          }`}>
            {ambiguities.length}
          </span>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3 min-h-[160px]">
        {loading ? (
          <div className="py-10 flex flex-col items-center justify-center text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs">Loading entities and alias maps...</p>
          </div>
        ) : activeTab === 'entities' ? (
          entities.length === 0 ? (
            <div className="py-10 border border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center text-slate-500 space-y-1">
              <p className="text-xs">No canonical entities registered in scope.</p>
              <p className="text-[11px] text-slate-600">Entities are created and resolved automatically during document ingestion.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1">
              {entities.map((e) => (
                <div
                  key={e.canonical_id}
                  className="bg-slate-850 border border-slate-750 rounded-xl p-3 space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-xs font-bold text-white">{e.name}</h4>
                      <p className="text-[10px] font-mono text-slate-400">{e.canonical_id}</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 font-mono">
                      {e.entity_type}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-1 pt-1">
                    <span className="text-[10px] text-slate-500">Aliases:</span>
                    {e.aliases.map((alias) => (
                      <span
                        key={alias}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                      >
                        {alias}
                      </span>
                    ))}
                    <span className="ml-auto text-[10px] text-emerald-400 font-mono">
                      Mentions: {e.mention_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          ambiguities.length === 0 ? (
            <div className="py-10 border border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center text-slate-500 space-y-1">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <p className="text-xs text-slate-400">Ambiguity review queue is clean.</p>
              <p className="text-[11px] text-slate-600">Borderline entity similarities will appear here for human sign-off.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
              {ambiguities.map((match) => (
                <div
                  key={match.id}
                  className="bg-slate-850 border border-amber-500/30 rounded-xl p-3.5 space-y-2.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-white">{match.mention_a}</span>
                      <span className="text-slate-500 font-mono">&harr;</span>
                      <span className="font-semibold text-white">{match.mention_b}</span>
                    </div>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Similarity: {Math.round(match.similarity_score * 100)}%
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    {match.reason}
                  </p>

                  <div className="flex items-center justify-end space-x-2 pt-1">
                    <button
                      onClick={() => handleResolve(match.id, 'REJECT_MERGE')}
                      disabled={resolvingId === match.id}
                      className="px-2.5 py-1 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors flex items-center space-x-1"
                    >
                      <X className="w-3 h-3 text-rose-400" />
                      <span>Keep Distinct</span>
                    </button>
                    <button
                      onClick={() => handleResolve(match.id, 'APPROVE_MERGE')}
                      disabled={resolvingId === match.id}
                      className="px-2.5 py-1 rounded-lg text-xs font-medium text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-colors flex items-center space-x-1"
                    >
                      <Check className="w-3 h-3 text-slate-950" />
                      <span>Approve Alias Merge</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
};
