export interface Session {
  session_id: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
}

export interface SessionStatus {
  session_id: string;
  status: string;
  stage: string;
  result?: any;
  error?: string;
  started_at: string;
  completed_at?: string;
}

export interface SessionResult {
  query_status?: string;
  query_resolution?: string;
  query_resolution_reason?: string;
  query_resolution_action?: string;
}

export interface FlowStage {
  name: string;
  status: 'pending' | 'active' | 'completed';
  description: string;
}