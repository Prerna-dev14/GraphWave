import React, { useEffect, useState } from 'react';
import { X, Hash, Bookmark, Copy, Check, FileCode2, GitBranch, Quote, CheckCircle2 } from 'lucide-react';
import { DocumentResponse, ChunkResponse, CandidateClaimResponse } from '../types/api';
import { fetchDocumentChunks, fetchDocumentClaims } from '../services/apiClient';

interface ChunkInspectorModalProps {
  document: DocumentResponse | null;
  tenantId: string;
  corpusId: string;
  onClose: () => void;
}

export const ChunkInspectorModal: React.FC<ChunkInspectorModalProps> = ({
  document,
  tenantId,
  corpusId,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'chunks' | 'claims'>('chunks');
  const [chunks, setChunks] = useState<ChunkResponse[]>([]);
  const [claims, setClaims] = useState<CandidateClaimResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!document) return;
    setLoading(true);
    Promise.all([
      fetchDocumentChunks(document.id, tenantId, corpusId),
      fetchDocumentClaims(document.id).catch(() => []),
    ])
      .then(([fetchedChunks, fetchedClaims]) => {
        setChunks(fetchedChunks);
        setClaims(fetchedClaims);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [document, tenantId, corpusId]);

  if (!document) return null;

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <FileCode2 className="w-5 h-5 text-brand-400" />
              <h3 className="text-base font-semibold text-white">{document.filename}</h3>
              <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                v{document.version}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">Document ID: {document.id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 border-b border-slate-800/80 bg-slate-850/50 flex space-x-4">
          <button
            onClick={() => setActiveTab('chunks')}
            className={`py-3 text-xs font-semibold border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'chunks'
                ? 'border-brand-500 text-brand-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>Deterministic Chunks</span>
            <span className="bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded-full text-[10px]">
              {chunks.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('claims')}
            className={`py-3 text-xs font-semibold border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'claims'
                ? 'border-brand-500 text-brand-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Extracted Candidate Claims</span>
            <span className="bg-brand-500/10 text-brand-400 border border-brand-500/20 px-1.5 py-0.2 rounded-full text-[10px]">
              {claims.length}
            </span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-500 space-y-2">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs">Loading inspection data...</p>
            </div>
          ) : activeTab === 'chunks' ? (
            chunks.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-8">No chunks found for this document.</p>
            ) : (
              chunks.map((c) => (
                <div
                  key={c.id}
                  className="bg-slate-850 border border-slate-750/70 rounded-xl p-4 space-y-2.5 transition-all hover:border-slate-700"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20 font-mono">
                        Chunk #{c.chunk_index}
                      </span>
                      {c.section_header && (
                        <span className="flex items-center space-x-1 text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                          <Bookmark className="w-3 h-3 text-slate-500" />
                          <span>{c.section_header}</span>
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleCopy(c.id)}
                      className="flex items-center space-x-1 text-[11px] font-mono text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 px-2 py-1 rounded transition-colors"
                      title="Copy Chunk ID"
                    >
                      <Hash className="w-3 h-3 text-brand-400" />
                      <span>{c.id.substring(0, 18)}...</span>
                      {copiedId === c.id ? (
                        <Check className="w-3 h-3 text-emerald-400 ml-1" />
                      ) : (
                        <Copy className="w-3 h-3 text-slate-500 ml-1" />
                      )}
                    </button>
                  </div>

                  <div className="bg-slate-900/90 rounded-lg p-3 text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed border border-slate-800">
                    {c.text}
                  </div>
                </div>
              ))
            )
          ) : (
            claims.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs space-y-1">
                <p>No candidate claims extracted for this document yet.</p>
                <p className="text-[11px] text-slate-600">Re-ingest the document to execute schema extraction.</p>
              </div>
            ) : (
              claims.map((claim) => (
                <div
                  key={claim.id}
                  className="bg-slate-850 border border-slate-750/70 rounded-xl p-4 space-y-3 hover:border-slate-700 transition-all"
                >
                  {/* Entity Triple Visualizer */}
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {/* Subject */}
                    <div className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 flex items-center space-x-1.5">
                      <span className="font-semibold text-white">{claim.subject}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({claim.subject_type})</span>
                    </div>

                    {/* Edge */}
                    <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20 font-mono text-[11px]">
                      <span>--[{claim.relation}]--&gt;</span>
                      <span className="text-emerald-400 font-semibold">{Math.round(claim.confidence * 100)}%</span>
                    </div>

                    {/* Object */}
                    <div className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 flex items-center space-x-1.5">
                      <span className="font-semibold text-white">{claim.object}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({claim.object_type})</span>
                    </div>

                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      {claim.status}
                    </span>
                  </div>

                  {/* Evidence Quote */}
                  <div className="bg-slate-900/90 rounded-lg p-2.5 text-xs text-slate-300 border border-slate-800/80 flex items-start space-x-2">
                    <Quote className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
                    <span className="italic leading-relaxed">{claim.evidence_text}</span>
                  </div>

                  {/* Provenance Footer */}
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span>Source Chunk: {claim.chunk_id.substring(0, 24)}...</span>
                    {claim.section_header && <span>Section: {claim.section_header}</span>}
                  </div>
                </div>
              ))
            )
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center text-xs text-slate-500">
          <span>{activeTab === 'chunks' ? `Chunks: ${chunks.length}` : `Candidate Claims: ${claims.length}`}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
