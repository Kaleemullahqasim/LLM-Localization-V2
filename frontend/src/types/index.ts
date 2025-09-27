/* eslint-disable @typescript-eslint/no-explicit-any */
export interface EvaluationRequest {
    source_text: string;
    target_text: string;
    source_language?: string;
    target_language?: string;
    locale: string;
    kb_version?: string;
}

export interface Finding {
    segment_id: string;
    rule_id: string;
    severity: 'Minor' | 'Major' | 'Critical';
    justification: string;
    penalty: number;
    citation: any;
    deterministic: boolean;
    span_start?: number;
    span_end?: number;
    highlighted_text?: string;
    dismissed?: boolean;
    accepted?: boolean;
    new_severity?: 'Minor' | 'Major' | 'Critical';
}

export interface ScoreBreakdown {
    penalty: number;
    count: number;
    rules_triggered: string[];
}

export interface ScoreReport {
    job_id: string;
    kb_version: string;
    rubric_version: string;
    model_prompt_version: string;
    final_score: number;
    findings: Finding[];
    by_macro: { [key: string]: ScoreBreakdown };
    source_text: string;
    target_text: string;
    locale: string;
}

export interface ReviewOverrideRequest {
    finding_id: string;
    action: 'accept' | 'dismiss' | 'change_severity';
    new_severity?: 'Minor' | 'Major' | 'Critical';
    reason?: string;
    reviewer: string;
}

export interface FeedbackEvent {
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
