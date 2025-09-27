import axios from 'axios';

// Define types inline to avoid import issues
interface EvaluationRequest {
    source_text: string;
    target_text: string;
    locale: string;
    kb_version?: string;
}

interface ScoreReport {
    job_id: string;
    kb_version: string;
    rubric_version: string;
    model_prompt_version: string;
    final_score: number;
    findings: any[];
    by_macro: { [key: string]: any };
    source_text: string;
    target_text: string;
    locale: string;
}

interface ReviewOverrideRequest {
    finding_id: string;
    action: 'accept' | 'dismiss' | 'change_severity';
    new_severity?: 'Minor' | 'Major' | 'Critical';
    reason?: string;
    reviewer: string;
}

interface FeedbackEvent {
    event_id: string;
    segment_id: string;
    rule_id: string;
    action: string;
    old_value: string;
    new_value: string;
    reason?: string;
    actor: string;
    created_at: string;
}

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const evaluateTranslation = async (request: EvaluationRequest): Promise<ScoreReport> => {
  const response = await apiClient.post('/evaluate', request);
  return response.data;
};

export const overrideFinding = async (request: ReviewOverrideRequest): Promise<FeedbackEvent> => {
    const response = await apiClient.post('/review/override', request);
    return response.data;
};

export const getKnowledgeBases = async (): Promise<any[]> => {
    const response = await apiClient.get('/knowledge-bases');
    return response.data.knowledge_bases;
};
