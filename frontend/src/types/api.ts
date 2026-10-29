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

export interface CandidateClaimResponse {
  id: string;
  subject: string;
  subject_type: string;
  relation: string;
  object: string;
  object_type: string;
  confidence: number;
  status: string;
  chunk_id: string;
  section_header: string | null;
  evidence_text: string;
}

export interface CanonicalEntityResponse {
  canonical_id: string;
  name: string;
  entity_type: string;
  tenant_id: string;
  corpus_id: string;
  aliases: string[];
  mention_count: number;
  created_at: string;
}

export interface AmbiguousMatch {
  id: string;
  mention_a: string;
  type_a: string;
  canonical_id_a: string;
  mention_b: string;
  type_b: string;
  canonical_id_b: string;
  similarity_score: number;
  status: string;
  reason: string;
  created_at: string;
}

export type RetrievalMode = 'hybrid' | 'vector' | 'graph';

export interface RetrievedChunkSchema {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  section_header: string | null;
  similarity_score: number;
  source: 'vector' | 'graph' | 'fused';
}

export interface TraversedEdgeSchema {
  source_entity: string;
  source_type: string;
  relation: string;
  target_entity: string;
  target_type: string;
  confidence: number;
  hop: number;
  source_chunk_ids: string[];
  evidence_text: string | null;
}

export interface RetrievalMetricsSchema {
  latency_vector_ms: number;
  latency_graph_ms: number;
  latency_fusion_ms: number;
  latency_total_ms: number;
  seed_chunks_count: number;
  graph_edges_count: number;
  fused_chunks_count: number;
}

export interface EvidenceBundleResponse {
  query: string;
  mode: RetrievalMode;
  tenant_id: string;
  corpus_id: string;
  seed_chunks: RetrievedChunkSchema[];
  graph_paths: TraversedEdgeSchema[];
  fused_evidence_chunks: RetrievedChunkSchema[];
  metrics: RetrievalMetricsSchema;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  section_header: string | null;
  snippet: string;
  document_version: string;
}

export interface QueryMetrics {
  latency_vector_ms: number;
  latency_graph_ms: number;
  latency_fusion_ms: number;
  latency_generation_ms: number;
  latency_total_ms: number;
  fused_chunks_count: number;
  graph_edges_count: number;
  citations_count: number;
  estimated_cost_usd: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  mode: RetrievalMode;
  tenant_id: string;
  corpus_id: string;
  trace_id: string;
  citations: Citation[];
  graph_paths: TraversedEdgeSchema[];
  metrics: QueryMetrics;
  created_at: string;
}

export interface RequestTraceResponse {
  request_id: string;
  tenant_id: string;
  corpus_id: string;
  query_text: string;
  retrieval_mode: string;
  retrieved_chunk_count: number;
  traversed_graph_nodes_count: number;
  latency_total_ms: number;
  latency_retrieval_ms: number;
  latency_generation_ms: number;
  created_at: string;
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

// Phase 6: Evaluation Benchmark Types
export interface TestCaseResult {
  test_case_id: string;
  category: string;
  hops: number;
  question: string;
  retrieval_mode: string;
  evidence_recall: number;
  citation_precision: number;
  answer_correctness: number;
  latency_ms: number;
  token_cost_usd: number;
  retrieved_chunks_count: number;
  traversed_paths_count: number;
  generated_answer: string;
  expected_answer: string;
  passed: boolean;
  notes?: string;
}

export interface EvaluationRunResponse {
  id: string;
  evaluation_dataset_version: string;
  retrieval_mode: string;
  answer_correctness: number;
  evidence_recall: number;
  citation_precision: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  token_cost_usd: number;
  total_questions: number;
  metrics_detail: TestCaseResult[];
  created_at: string;
}

export interface EvaluationComparisonResponse {
  dataset_version: string;
  timestamp: string;
  runs: EvaluationRunResponse[];
  recommended_mode: string;
  analysis_summary: string;
}

