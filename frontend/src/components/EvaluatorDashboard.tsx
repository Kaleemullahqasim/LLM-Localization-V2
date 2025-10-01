import { useState, useEffect } from 'react';
import axios from 'axios';

interface Evaluation {
  job_id: string;
  final_score: number;
  source_text: string;
  target_text: string;
  findings: Finding[];
  kb_version: string;
  created_at: string;
}

interface Finding {
  segment_id: string;
  rule_id: string;
  severity: string;
  penalty: number;
  justification: string;
  highlighted_text: string;
  span_start: number;
  span_end: number;
  reviewer_action?: string;
  reviewer_comment?: string;
}

const styles = {
  container: {
    maxWidth: '1800px',
    margin: '0 auto',
    padding: '2.5rem 2rem'
  },
  card: {
    background: 'white',
    borderRadius: '0.75rem',
    padding: '2rem',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    border: '1px solid #e2e8f0'
  },
  input: {
    width: '100%',
    padding: '0.75rem 1rem',
    border: '1px solid #e2e8f0',
    borderRadius: '0.5rem',
    fontSize: '0.9375rem',
    color: '#1e293b',
    background: 'white',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    outline: 'none',
    fontFamily: 'inherit',
    resize: 'vertical' as const
  }
};

export default function EvaluatorDashboard() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [selectedEval, setSelectedEval] = useState<Evaluation | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchEvaluations();
  }, []);

  const fetchEvaluations = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/evaluations');
      setEvaluations(response.data.evaluations || []);
    } catch (err) {
      console.error('Failed to fetch evaluations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOverride = async (findingIndex: number, action: 'accept' | 'dismiss' | 'escalate', comment: string) => {
    if (!selectedEval) return;

    try {
      await axios.post('http://localhost:8000/api/review/override', {
        job_id: selectedEval.job_id,
        finding_id: selectedEval.findings[findingIndex].rule_id,
        segment_id: selectedEval.findings[findingIndex].segment_id,
        action: action,
        comment: comment,
        reviewer: 'evaluator'
      });

      const response = await axios.get(`http://localhost:8000/api/evaluation/${selectedEval.job_id}`);
      setSelectedEval(response.data);
      setEvaluations(prev => prev.map(e => e.job_id === selectedEval.job_id ? response.data : e));
    } catch (err) {
      console.error('Failed to override:', err);
    }
  };

  return (
    <div style={styles.container}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', color: '#1e293b', marginBottom: '0.5rem' }}>
          Evaluator Dashboard
        </h2>
        <p style={{ color: '#64748b', fontSize: '1rem' }}>
          Review AI evaluations and provide expert oversight for quality assurance
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '2rem' }}>
        {/* Left Panel - Evaluation List */}
        <div style={styles.card}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#1e293b' }}>
            Pending Reviews
            <span style={{
              marginLeft: '0.5rem',
              padding: '0.25rem 0.75rem',
              background: '#10b98115',
              color: '#10b981',
              borderRadius: '1rem',
              fontSize: '0.8125rem',
              fontWeight: '600'
            }}>
              {evaluations.length}
            </span>
          </h3>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
              Loading...
            </div>
          ) : evaluations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
              <p style={{ fontSize: '0.9375rem', color: '#475569' }}>No evaluations to review yet</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {evaluations.map((evaluation) => (
                <button
                  key={evaluation.job_id}
                  onClick={() => setSelectedEval(evaluation)}
                  style={{
                    padding: '1rem',
                    border: selectedEval?.job_id === evaluation.job_id ? '2px solid #10b981' : '1px solid #e2e8f0',
                    borderRadius: '0.5rem',
                    background: selectedEval?.job_id === evaluation.job_id ? '#f0fdf4' : 'white',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedEval?.job_id !== evaluation.job_id) {
                      e.currentTarget.style.borderColor = '#cbd5e1';
                      e.currentTarget.style.background = '#fafbfc';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedEval?.job_id !== evaluation.job_id) {
                      e.currentTarget.style.borderColor = '#e2e8f0';
                      e.currentTarget.style.background = 'white';
                    }
                  }}
                >
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#1e293b', fontSize: '0.9375rem' }}>
                    Score: {evaluation.final_score}/100
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                    {evaluation.findings.length} issues · {new Date(evaluation.created_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Details */}
        <div style={styles.card}>
          {!selectedEval ? (
            <div style={{ textAlign: 'center', padding: '6rem', color: '#94a3b8' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>👈</div>
              <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#475569', marginBottom: '0.5rem' }}>
                Select an evaluation
              </h4>
              <p style={{ fontSize: '0.9375rem' }}>
                Choose an evaluation from the list to review findings
              </p>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1e293b' }}>
                    Review Evaluation
                  </h3>
                  <div style={{
                    padding: '0.625rem 1.25rem',
                    borderRadius: '0.5rem',
                    background: selectedEval.final_score >= 90 ? '#d1fae5' : selectedEval.final_score >= 80 ? '#dbeafe' : '#fed7aa',
                    color: selectedEval.final_score >= 90 ? '#065f46' : selectedEval.final_score >= 80 ? '#1e40af' : '#92400e',
                    fontWeight: '600',
                    fontSize: '1rem'
                  }}>
                    {selectedEval.final_score}/100
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #f1f5f9' }}>
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}>
                      Source
                    </div>
                    <div style={{ color: '#1e293b', fontSize: '0.9375rem', lineHeight: 1.6 }}>
                      {selectedEval.source_text}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}>
                      Target
                    </div>
                    <div style={{ color: '#1e293b', fontSize: '0.9375rem', lineHeight: 1.6 }}>
                      {selectedEval.target_text}
                    </div>
                  </div>
                </div>
              </div>

              <h4 style={{ fontWeight: '600', marginBottom: '1rem', color: '#1e293b', fontSize: '1rem' }}>
                Findings to Review ({selectedEval.findings.length})
              </h4>

              {selectedEval.findings.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#475569', marginBottom: '0.5rem' }}>
                    Perfect translation!
                  </h4>
                  <p style={{ fontSize: '0.9375rem' }}>No issues detected by the AI system</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {selectedEval.findings.map((finding, idx) => (
                    <FindingCard
                      key={idx}
                      finding={finding}
                      index={idx}
                      onOverride={handleOverride}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FindingCard({ finding, index, onOverride }: { finding: Finding, index: number, onOverride: (idx: number, action: any, comment: string) => void }) {
  const [comment, setComment] = useState('');
  const [showActions, setShowActions] = useState(false);

  return (
    <div style={{
      padding: '1.5rem',
      border: '1px solid #e2e8f0',
      borderRadius: '0.75rem',
      background: finding.reviewer_action ? '#f0fdf4' : 'white',
      transition: 'all 0.2s'
    }}>
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <span style={{
          padding: '0.375rem 0.875rem',
          borderRadius: '0.375rem',
          fontSize: '0.8125rem',
          fontWeight: '600',
          background: finding.severity === 'Critical' ? '#fef2f2' : finding.severity === 'Major' ? '#fef3c7' : '#e0f2fe',
          color: finding.severity === 'Critical' ? '#dc2626' : finding.severity === 'Major' ? '#d97706' : '#0284c7'
        }}>
          {finding.severity}
        </span>
        <span style={{ fontSize: '0.875rem', color: '#64748b', padding: '0.375rem 0' }}>
          -{finding.penalty} pts
        </span>
        {finding.reviewer_action && (
          <span style={{
            padding: '0.375rem 0.875rem',
            borderRadius: '0.375rem',
            fontSize: '0.8125rem',
            fontWeight: '600',
            background: '#d1fae5',
            color: '#065f46'
          }}>
            ✓ {finding.reviewer_action.toUpperCase()}
          </span>
        )}
      </div>

      <p style={{ marginBottom: '0.75rem', color: '#475569', fontSize: '0.9375rem', lineHeight: 1.6 }}>
        {finding.justification}
      </p>
      
      {finding.highlighted_text && (
        <div style={{
          padding: '0.75rem',
          background: '#fef3c7',
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          marginBottom: '1rem',
          border: '1px solid #fde68a'
        }}>
          <span style={{ fontWeight: '600', color: '#92400e' }}>Highlighted:</span>{' '}
          <span style={{ color: '#78350f' }}>"{finding.highlighted_text}"</span>
        </div>
      )}

      {finding.reviewer_comment && (
        <div style={{
          padding: '1rem',
          background: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          marginBottom: '1rem',
          color: '#166534'
        }}>
          <strong>Reviewer Note:</strong> {finding.reviewer_comment}
        </div>
      )}

      {!finding.reviewer_action && (
        <>
          <button
            onClick={() => setShowActions(!showActions)}
            style={{
              padding: '0.625rem 1.25rem',
              background: showActions ? '#f1f5f9' : '#10b981',
              color: showActions ? '#475569' : 'white',
              border: showActions ? '1px solid #e2e8f0' : 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!showActions) {
                e.currentTarget.style.background = '#059669';
              }
            }}
            onMouseLeave={(e) => {
              if (!showActions) {
                e.currentTarget.style.background = '#10b981';
              }
            }}
          >
            {showActions ? '✕ Cancel' : '✏️ Review This'}
          </button>

          {showActions && (
            <div style={{ marginTop: '1rem', padding: '1.25rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #f1f5f9' }}>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add your comment (optional)..."
                rows={2}
                style={{
                  ...styles.input,
                  marginBottom: '0.75rem'
                }}
              />
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  onClick={() => { onOverride(index, 'accept', comment); setShowActions(false); }}
                  style={{
                    padding: '0.625rem 1.25rem',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '0.875rem',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#059669'}
                  onMouseLeave={(e) => e.currentTarget.style.background = '#10b981'}
                >
                  ✓ Accept
                </button>
                <button
                  onClick={() => { onOverride(index, 'dismiss', comment); setShowActions(false); }}
                  style={{
                    padding: '0.625rem 1.25rem',
                    background: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '0.875rem',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#dc2626'}
                  onMouseLeave={(e) => e.currentTarget.style.background = '#ef4444'}
                >
                  ✕ Dismiss
                </button>
                <button
                  onClick={() => { onOverride(index, 'escalate', comment); setShowActions(false); }}
                  style={{
                    padding: '0.625rem 1.25rem',
                    background: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '0.875rem',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#d97706'}
                  onMouseLeave={(e) => e.currentTarget.style.background = '#f59e0b'}
                >
                  ⚠ Escalate
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
