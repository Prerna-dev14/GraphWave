import { DocumentListResponse, ChunkResponse, IngestionJobResponse, ReadyHealthResponse } from '../types/api';

const BASE_URL = '';

export async function fetchHealth(): Promise<ReadyHealthResponse> {
  const resp = await fetch(`${BASE_URL}/health/ready`);
  if (!resp.ok) {
    throw new Error(`Health check failed with status ${resp.status}`);
  }
  return resp.json();
}

export async function listDocuments(tenantId: string, corpusId: string): Promise<DocumentListResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/documents?tenant_id=${encodeURIComponent(tenantId)}&corpus_id=${encodeURIComponent(corpusId)}`);
  if (!resp.ok) {
    throw new Error(`Failed to list documents: ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchDocumentChunks(
  docId: string,
  tenantId: string,
  corpusId: string
): Promise<ChunkResponse[]> {
  const resp = await fetch(
    `${BASE_URL}/api/v1/documents/${encodeURIComponent(docId)}/chunks?tenant_id=${encodeURIComponent(tenantId)}&corpus_id=${encodeURIComponent(corpusId)}`
  );
  if (!resp.ok) {
    throw new Error(`Failed to fetch chunks: ${resp.statusText}`);
  }
  return resp.json();
}

export interface IngestPayload {
  filename: string;
  content: string;
  version?: string;
  tenant_id: string;
  corpus_id: string;
}

export async function ingestDocument(payload: IngestPayload): Promise<IngestionJobResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const errorBody = await resp.json().catch(() => null);
    throw new Error(errorBody?.message || `Ingestion failed with status ${resp.status}`);
  }
  return resp.json();
}

export async function fetchJobStatus(jobId: string): Promise<IngestionJobResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/ingestion-jobs/${encodeURIComponent(jobId)}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch job ${jobId}`);
  }
  return resp.json();
}
