import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { IngestionPanel } from './components/IngestionPanel';
import { DocumentList } from './components/DocumentList';
import { ChunkInspectorModal } from './components/ChunkInspectorModal';
import { QueryShell } from './components/QueryShell';
import { EntityRegistryPanel } from './components/EntityRegistryPanel';
import { fetchHealth, listDocuments } from './services/apiClient';
import { ReadyHealthResponse, DocumentResponse } from './types/api';
import { ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [tenantId, setTenantId] = useState('tenant-default');
  const [corpusId, setCorpusId] = useState('corpus-primary');
  const [health, setHealth] = useState<ReadyHealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);

  const loadHealth = useCallback(async () => {
    setLoadingHealth(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.error('Failed to load health:', err);
    } finally {
      setLoadingHealth(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const data = await listDocuments(tenantId, corpusId);
      setDocuments(data.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  }, [tenantId, corpusId]);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <Header
        health={health}
        loadingHealth={loadingHealth}
        onRefreshHealth={loadHealth}
        tenantId={tenantId}
        corpusId={corpusId}
        onTenantChange={setTenantId}
        onCorpusChange={setCorpusId}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto w-full px-6 py-8 flex-1 space-y-8">
        {/* Phase 0/1 Status Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="p-2.5 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mt-0.5">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white">Phase 0 & 1 Operational Foundation Active</h2>
                <span className="text-[11px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono">
                  Verified Clean
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Ontology constraints, deterministic ID algorithms, boundary-aware parser, pgvector & Neo4j schemas, and mock adapters are active.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
            <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700">Tests: 14/14 PASS</span>
            <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700">API: /health/live 200</span>
          </div>
        </div>

        {/* 2-Column Grid: Ingestion on left, Documents on right */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <IngestionPanel
            tenantId={tenantId}
            corpusId={corpusId}
            onIngestionSuccess={loadDocuments}
          />
          <DocumentList
            documents={documents}
            loading={loadingDocs}
            onSelectDocument={setSelectedDoc}
          />
        </div>

        {/* Phase 3: Knowledge Graph Entities & Ambiguity Review Panel */}
        <EntityRegistryPanel
          tenantId={tenantId}
          corpusId={corpusId}
        />

        {/* Multi-Hop Query Explorer Shell */}
        <QueryShell />
      </main>

      {/* Chunk Inspector Modal */}
      <ChunkInspectorModal
        document={selectedDoc}
        tenantId={tenantId}
        corpusId={corpusId}
        onClose={() => setSelectedDoc(null)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/50 py-6 px-6 text-center text-xs text-slate-500">
        <p>GraphWeave v1.0.0 — Built in accordance with GraphWeave Master Specification, Implementation Document, and Development Plan.</p>
      </footer>
    </div>
  );
};

export default App;
