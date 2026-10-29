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

export async function fetchDocumentClaims(docId: string): Promise<import('../types/api').CandidateClaimResponse[]> {
  const resp = await fetch(`${BASE_URL}/api/v1/documents/${encodeURIComponent(docId)}/claims`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch claims for doc ${docId}`);
  }
  return resp.json();
}

export async function listCanonicalEntities(
  tenantId: string,
  corpusId: string
): Promise<import('../types/api').CanonicalEntityResponse[]> {
  const resp = await fetch(
    `${BASE_URL}/api/v1/entities?tenant_id=${encodeURIComponent(tenantId)}&corpus_id=${encodeURIComponent(corpusId)}`
  );
  if (!resp.ok) {
    throw new Error('Failed to list canonical entities');
  }
  return resp.json();
}

export async function listAmbiguities(): Promise<import('../types/api').AmbiguousMatch[]> {
  const resp = await fetch(`${BASE_URL}/api/v1/entities/ambiguities`);
  if (!resp.ok) {
    throw new Error('Failed to fetch ambiguities');
  }
  return resp.json();
}

export async function resolveAmbiguity(matchId: string, action: 'APPROVE_MERGE' | 'REJECT_MERGE') {
  const resp = await fetch(`${BASE_URL}/api/v1/entities/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ match_id: matchId, action }),
  });
  if (!resp.ok) {
    throw new Error('Failed to resolve ambiguity');
  }
  return resp.json();
}

export interface RetrieveParams {
  query: string;
  mode: import('../types/api').RetrievalMode;
  tenant_id: string;
  corpus_id: string;
  top_k_vector?: number;
  max_depth?: number;
  max_fan_out?: number;
}

export async function executeRetrieve(params: RetrieveParams): Promise<import('../types/api').EvidenceBundleResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    const errorBody = await resp.json().catch(() => null);
    throw new Error(errorBody?.message || `Retrieval failed with status ${resp.status}`);
  }
  return resp.json();
}

export interface QueryParams {
  query: string;
  mode: import('../types/api').RetrievalMode;
  tenant_id: string;
  corpus_id: string;
  max_depth?: number;
  max_fan_out?: number;
}

export async function executeQuery(params: QueryParams): Promise<import('../types/api').QueryResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    const errorBody = await resp.json().catch(() => null);
    throw new Error(errorBody?.message || `Query failed with status ${resp.status}`);
  }
  return resp.json();
}

export async function fetchRequestTrace(traceId: string): Promise<import('../types/api').RequestTraceResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/requests/${encodeURIComponent(traceId)}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch trace ${traceId}`);
  }
  return resp.json();
}
