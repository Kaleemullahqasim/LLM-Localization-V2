import { useState, useEffect } from 'react';
import axios from 'axios';

interface ScoreReport {
  job_id: string;
  final_score: number;
  findings: any[];
  by_macro: any;
  kb_version: string;
  created_at: string;
  source_text: string;
  target_text: string;
}

const styles = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '2.5rem 2rem'
  },
  card: {
    background: 'white',
    borderRadius: '0.75rem',
    padding: '2rem',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
    border: '1px solid #e2e8f0',
    marginBottom: '2rem'
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
    fontFamily: 'inherit'
  } as React.CSSProperties,
  button: {
    padding: '0.875rem 1.5rem',
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    fontSize: '0.9375rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 2px 4px rgba(59, 130, 246, 0.2)'
  } as React.CSSProperties
};

export default function TestTakerDashboard() {
  const [sourceText, setSourceText] = useState('');
  const [targetText, setTargetText] = useState('');
  const [locale, setLocale] = useState('zh-CN');
  const [kbVersion, setKbVersion] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [scoreReport, setScoreReport] = useState<ScoreReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/knowledge-bases');
      const kbs = response.data.knowledge_bases;
      setKnowledgeBases(kbs);
      if (kbs.length > 0) {
        setKbVersion(kbs[0].kb_version);
      }
    } catch (err) {
      console.error('Failed to fetch KBs:', err);
    }
  };

  const handleSubmitTest = async () => {
    if (!kbVersion) {
      setError('Please select a knowledge base');
      return;
    }

    setIsEvaluating(true);
    setError(null);
    setScoreReport(null);

    try {
      const response = await axios.post('http://localhost:8000/api/evaluate', {
        source_text: sourceText,
        target_text: targetText,
        locale: locale,
        kb_version: kbVersion,
      });
      setScoreReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setIsEvaluating(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 95) return { bg: '#d1fae5', text: '#065f46', label: '🎉 Excellent' };
    if (score >= 90) return { bg: '#dbeafe', text: '#1e40af', label: '✅ Great' };
    if (score >= 80) return { bg: '#fef3c7', text: '#92400e', label: '👍 Good' };
    return { bg: '#fee2e2', text: '#991b1b', label: '⚠️ Needs Work' };
  };

  return (
    <div style={styles.container}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', color: '#1e293b', marginBottom: '0.5rem' }}>
          Submit Translation Test
        </h2>
        <p style={{ color: '#64748b', fontSize: '1rem' }}>
          Submit your translation for instant AI-powered quality assessment
        </p>
      </div>

      {/* Submission Form */}
      <div style={styles.card}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#1e293b' }}>
          Translation Submission
        </h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#334155', fontSize: '0.875rem' }}>
            Source Text (English)
          </label>
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Enter the original text in English..."
            rows={4}
            style={styles.input}
            onFocus={(e: any) => {
              e.target.style.borderColor = '#3b82f6';
              e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            }}
            onBlur={(e: any) => {
              e.target.style.borderColor = '#e2e8f0';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#334155', fontSize: '0.875rem' }}>
            Your Translation
          </label>
          <textarea
            value={targetText}
            onChange={(e) => setTargetText(e.target.value)}
            placeholder="Enter your translation..."
            rows={4}
            style={styles.input}
            onFocus={(e: any) => {
              e.target.style.borderColor = '#3b82f6';
              e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            }}
            onBlur={(e: any) => {
              e.target.style.borderColor = '#e2e8f0';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#334155', fontSize: '0.875rem' }}>
              Target Locale
            </label>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              style={styles.input}
              onFocus={(e: any) => {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
              }}
              onBlur={(e: any) => {
                e.target.style.borderColor = '#e2e8f0';
                e.target.style.boxShadow = 'none';
              }}
            >
              <option value="zh-CN">Chinese (Simplified)</option>
              <option value="zh-TW">Chinese (Traditional)</option>
              <option value="ja-JP">Japanese</option>
              <option value="ko-KR">Korean</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#334155', fontSize: '0.875rem' }}>
              Knowledge Base
            </label>
            <select
              value={kbVersion}
              onChange={(e) => setKbVersion(e.target.value)}
              style={styles.input}
              onFocus={(e: any) => {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
              }}
              onBlur={(e: any) => {
                e.target.style.borderColor = '#e2e8f0';
                e.target.style.boxShadow = 'none';
              }}
            >
              {knowledgeBases.map(kb => (
                <option key={kb.kb_version} value={kb.kb_version}>
                  {kb.source_document} ({kb.rule_count} rules)
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div style={{
            padding: '1rem',
            background: '#fef2f2',
            color: '#dc2626',
            borderRadius: '0.5rem',
            marginBottom: '1rem',
            border: '1px solid #fecaca',
            fontSize: '0.9375rem'
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleSubmitTest}
          disabled={isEvaluating || !sourceText || !targetText}
          style={{
            ...styles.button,
            width: '100%',
            opacity: isEvaluating || !sourceText || !targetText ? 0.5 : 1,
            cursor: isEvaluating || !sourceText || !targetText ? 'not-allowed' : 'pointer'
          }}
          onMouseEnter={(e) => {
            if (!isEvaluating && sourceText && targetText) {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(59, 130, 246, 0.3)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 2px 4px rgba(59, 130, 246, 0.2)';
          }}
        >
          {isEvaluating ? '🔄 Evaluating...' : '✅ Submit Translation'}
        </button>
      </div>

      {/* Results */}
      {scoreReport && (
        <div style={styles.card}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#1e293b' }}>
            Evaluation Results
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', marginBottom: '2rem' }}>
            <div style={{
              width: '140px',
              height: '140px',
              borderRadius: '50%',
              background: scoreReport.final_score >= 90 ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 
                          scoreReport.final_score >= 80 ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' :
                          'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '3rem',
              fontWeight: 'bold',
              boxShadow: '0 10px 30px rgba(0,0,0,0.15)'
            }}>
              {scoreReport.final_score}
              <span style={{ fontSize: '0.875rem', fontWeight: 'normal' }}>/ 100</span>
            </div>

            <div style={{ flex: 1 }}>
              <div style={{
                display: 'inline-block',
                padding: '0.625rem 1.25rem',
                background: getScoreColor(scoreReport.final_score).bg,
                color: getScoreColor(scoreReport.final_score).text,
                borderRadius: '0.5rem',
                fontWeight: '600',
                fontSize: '1.125rem',
                marginBottom: '1rem'
              }}>
                {getScoreColor(scoreReport.final_score).label}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.9375rem' }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong style={{ color: '#475569' }}>Issues Found:</strong> {scoreReport.findings.length}
                </div>
                <div style={{ fontSize: '0.875rem' }}>
                  Job ID: <code style={{ background: '#f1f5f9', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                    {scoreReport.job_id}
                  </code>
                </div>
              </div>
            </div>
          </div>

          {scoreReport.findings.length > 0 && (
            <div>
              <h4 style={{ fontWeight: '600', marginBottom: '1rem', color: '#1e293b', fontSize: '1rem' }}>
                Issues Detected:
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {scoreReport.findings.map((finding, idx) => (
                  <div key={idx} style={{
                    padding: '1.25rem',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.5rem',
                    background: '#fafbfc'
                  }}>
                    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.75rem' }}>
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
                      <span style={{ fontSize: '0.875rem', color: '#64748b' }}>-{finding.penalty} points</span>
                    </div>
                    <p style={{ color: '#475569', fontSize: '0.9375rem', lineHeight: 1.6 }}>{finding.justification}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{
            marginTop: '1.5rem',
            padding: '1.25rem',
            background: '#eff6ff',
            borderRadius: '0.5rem',
            fontSize: '0.875rem',
            color: '#1e40af',
            border: '1px solid #dbeafe'
          }}>
            <strong>📝 Note:</strong> Your submission has been sent to evaluators for review. They may adjust the score based on context and additional considerations.
          </div>
        </div>
      )}
    </div>
  );
}
