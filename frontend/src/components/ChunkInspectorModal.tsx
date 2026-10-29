import React, { useEffect, useState } from 'react';
import { X, Hash, Bookmark, Copy, Check, FileCode2 } from 'lucide-react';
import { DocumentResponse, ChunkResponse } from '../types/api';
import { fetchDocumentChunks } from '../services/apiClient';

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
  const [chunks, setChunks] = useState<ChunkResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!document) return;
    setLoading(true);
    fetchDocumentChunks(document.id, tenantId, corpusId)
      .then(setChunks)
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

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-500 space-y-2">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs">Loading deterministic chunks...</p>
            </div>
          ) : chunks.length === 0 ? (
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
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/50 flex justify-between items-center text-xs text-slate-500">
          <span>Total Chunks: {chunks.length}</span>
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
