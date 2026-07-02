export type UserRole = "admin" | "analyst" | "viewer";
export type Organism = "pf" | "pv" | "ag" | "other";
export type JobStatus = "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
export type WorkflowType =
  | "single_qc"
  | "single_full"
  | "pop_joint"
  | "pop_structure"
  | "pop_phylo"
  | "pop_selection"
  | "pop_full";
export type FileType = "fastq_r1" | "fastq_r2" | "fastq_single" | "bam" | "vcf" | "other";
export type UploadStatus = "uploading" | "completed" | "failed";
export type ResultType =
  | "qc_report"
  | "alignment_stats"
  | "variant_calls"
  | "annotated_variants"
  | "fws"
  | "ibd_matrix"
  | "admixture"
  | "phylogenetic_tree"
  | "diversity_stats"
  | "selection_scan"
  | "full_report"
  | "other";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  profile: { institution: string; max_concurrent_jobs: number; storage_quota_gb: number } | null;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  organism: Organism;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface Sample {
  id: string;
  project_id: string;
  sample_id: string;
  external_id: string;
  species: Organism;
  collection_date: string | null;
  collection_location: string;
  latitude: number | null;
  longitude: number | null;
  metadata: Record<string, unknown>;
  notes: string;
  created_at: string;
}

export interface RawFile {
  id: string;
  sample_id: string;
  original_filename: string;
  file_type: FileType;
  file_size_bytes: number;
  md5_checksum: string;
  is_validated: boolean;
  upload_status: UploadStatus;
  uploaded_at: string;
}

export interface AnalysisJob {
  id: string;
  name: string;
  workflow_type: WorkflowType;
  status: JobStatus;
  parameters: Record<string, unknown>;
  progress_percent: number;
  celery_task_id: string;
  submitted_by_id: string;
  submitted_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string;
  execution_log: string;
}

export interface Result {
  id: string;
  job_id: string;
  result_type: ResultType;
  minio_object_key: string;
  summary_data: Record<string, unknown>;
  created_at: string;
}

export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  timestamp: string;
  checks: Record<string, { status: string; latency_ms?: number; error?: string }>;
}
