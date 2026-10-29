export type JobStatus = 'PENDING' | 'PROCESSING' | 'PARSED' | 'EXTRACTING' | 'INDEXED' | 'COMPLETED' | 'FAILED';

export interface DocumentResponse {
  id: string;
  tenant_id: string;
  corpus_id: string;
  filename: string;
  content_type: string;
  version: string;
  chunk_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total_count: number;
  tenant_id: string;
  corpus_id: string;
}

export interface ChunkResponse {
  id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  section_header: string | null;
  page_number: number | null;
  created_at: string;
}

export interface IngestionJobResponse {
  job_id: string;
  document_id: string;
  filename: string;
  status: JobStatus;
  chunk_count: number;
  extracted_entities_count: number;
  extracted_relations_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ServiceDependencyStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  details?: string;
}

export interface ReadyHealthResponse {
  status: 'ready' | 'not_ready';
  service: string;
  version: string;
  timestamp: string;
  dependencies: {
    postgresql: ServiceDependencyStatus;
    neo4j: ServiceDependencyStatus;
  };
}
