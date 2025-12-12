export interface Party {
  name: string;
  role?: string;
}

export interface ExtractedData {
  parties: Party[];
  effective_date?: string;
  contract_duration_months?: number;
  contract_duration_raw?: string;
  jurisdiction?: string;
  risk_score: number;
}

export interface ValidationIssue {
  field: string;
  rule: string;
  message: string;
  severity: 'warning' | 'error' | 'critical';
  reasoning?: string;
}

export type ContractStatus =
  | 'pending'
  | 'processing'
  | 'approved'
  | 'requires_human_review'
  | 'rejected';

export interface Contract {
  id: string;
  file_name: string;
  status: ContractStatus;
  created_at: string;
  processed_at?: string;
  extracted_data?: ExtractedData;
  validation_issues: ValidationIssue[];
  requires_human_review: boolean;
  review_reasons: string[];
  confidence_score?: number;
  human_approved: boolean;
}

export interface ContractListResponse {
  contracts: Contract[];
  total: number;
}

export interface AuditResponse {
  id: string;
  status: ContractStatus;
  extracted_data: ExtractedData;
  validation_issues: ValidationIssue[];
  requires_human_review: boolean;
  review_reasons: string[];
  confidence_score: number;
  processing_time_ms: number;
}
