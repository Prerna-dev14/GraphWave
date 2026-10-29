import React from 'react';
import { Layers, FileText, ChevronRight, FolderOpen, Calendar } from 'lucide-react';
import { DocumentResponse } from '../types/api';

interface DocumentListProps {
  documents: DocumentResponse[];
  loading: boolean;
  onSelectDocument: (doc: DocumentResponse) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  loading,
  onSelectDocument,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-semibold text-white">Corpus Documents</h2>
        </div>
        <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700">
          {documents.length} Ingested
        </span>
      </div>

      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center text-slate-500 space-y-2">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs">Fetching scoped corpus documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="py-12 border border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center text-slate-500 space-y-2">
          <FolderOpen className="w-8 h-8 stroke-1" />
          <p className="text-xs">No documents found in this tenant/corpus scope.</p>
          <p className="text-[11px] text-slate-600">Select a benchmark sample above to ingest your first document.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/80">
          {documents.map((doc) => (
            <div
              key={doc.id}
              onClick={() => onSelectDocument(doc)}
              className="py-3 px-3 -mx-3 rounded-xl hover:bg-slate-850 cursor-pointer transition-colors flex items-center justify-between group"
            >
              <div className="flex items-start space-x-3">
                <div className="p-2 rounded-lg bg-slate-800 text-slate-300 group-hover:text-brand-400 transition-colors mt-0.5">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-medium text-white group-hover:text-brand-300 transition-colors">
                      {doc.filename}
                    </h3>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                      v{doc.version}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                    <span className="font-mono text-[11px] text-slate-400">ID: {doc.id.substring(0, 12)}...</span>
                    <span>•</span>
                    <span className="text-brand-400 font-mono text-[11px]">{doc.chunk_count} Chunks</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-[11px]">
                      <Calendar className="w-3 h-3" />
                      {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 text-slate-500 group-hover:text-white transition-colors">
                <span className="text-xs font-medium hidden sm:inline">Inspect Chunks</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
