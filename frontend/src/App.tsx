import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// --- Data Types (mirroring backend models) ---

interface Citation {
  section_path: string[];
  document_name?: string;
}

enum Severity {
  MINOR = "Minor",
  MAJOR = "Major",
  CRITICAL = "Critical",
}

interface Finding {
  segment_id: string;
  rule_id: string;
  severity: Severity;
  penalty: number;
  justification: string;
  citation: Citation;
  deterministic: boolean;
  span_start?: number;
  span_end?: number;
  highlighted_text?: string;
  // Frontend-specific state
  override_severity?: Severity;
  dismissed?: boolean;
  accepted?: boolean;
}

interface ScoreBreakdown {
  penalty: number;
  count: number;
  rules_triggered: string[];
}

interface ScoreReport {
  job_id: string;
  kb_version: string;
  rubric_version: string;
  final_score: number;
  findings: Finding[];
  by_macro: { [key: string]: ScoreBreakdown };
  source_text: string;
  target_text: string;
  locale: string;
}

interface KnowledgeBaseInfo {
    kb_version: string;
    locale: string;
    rule_count: number;
    source_document: string;
    created_at: string;
}


function App() {
  const [sourceText, setSourceText] = useState('Welcome to Shopify!');
  const [targetText, setTargetText] = useState('欢迎使用Shopify!');
  const [locale, setLocale] = useState('zh-CN');
  const [kbVersion, setKbVersion] = useState('');
  
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseInfo[]>([]);
  const [scoreReport, setScoreReport] = useState<ScoreReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch available knowledge bases on component mount
    const fetchKBs = async () => {
      try {
        const response = await axios.get('/api/knowledge-bases');
        setKnowledgeBases(response.data.knowledge_bases);
        // Auto-select the first KB if available
        if (response.data.knowledge_bases.length > 0) {
          setKbVersion(response.data.knowledge_bases[0].kb_version);
        }
      } catch (err) {
        setError('Failed to fetch knowledge bases. Is the backend running?');
      }
    };
    fetchKBs();
  }, []);

  const handleEvaluate = async () => {
    if (!kbVersion) {
      setError('Please select a Knowledge Base.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setScoreReport(null);

    try {
      const response = await axios.post<ScoreReport>('/api/evaluate', {
        source_text: sourceText,
        target_text: targetText,
        locale: locale,
        kb_version: kbVersion,
      });
      setScoreReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An unknown error occurred during evaluation.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOverride = (findingId: string, action: string, newSeverity?: Severity) => {
    // This is a placeholder for the review functionality.
    // In a real app, this would make an API call to /api/review/override
    // and then update the scoreReport state.
    console.log(`Override action: ${action} for finding ${findingId} with new severity ${newSeverity}`);
    
    if (scoreReport) {
        const updatedFindings = scoreReport.findings.map(f => {
            if (f.segment_id === findingId) {
                if (action === 'dismiss') {
                    return { ...f, dismissed: !f.dismissed };
                }
                if (action === 'accept') {
                    return { ...f, accepted: !f.accepted };
                }
                if (action === 'change_severity' && newSeverity) {
                    return { ...f, override_severity: newSeverity };
                }
            }
            return f;
        });
        setScoreReport({ ...scoreReport, findings: updatedFindings });
    }
  };

  const getSeverityClass = (severity: Severity) => {
    switch (severity) {
      case Severity.CRITICAL: return 'severity-critical';
      case Severity.MAJOR: return 'severity-major';
      case Severity.MINOR: return 'severity-minor';
      default: return '';
    }
  };
  
  const renderHighlightedTextWithFindings = (text: string, findings: Finding[]) => {
    if (!findings || findings.length === 0) {
      return text;
    }
    
    // Sort findings by span_start to apply highlights in order
    const sortedFindings = findings
      .filter(f => f.span_start !== undefined && f.span_end !== undefined)
      .sort((a, b) => (a.span_start || 0) - (b.span_start || 0));
    
    if (sortedFindings.length === 0) {
      return text;
    }
    
    let result = [];
    let lastIndex = 0;
    
    for (const finding of sortedFindings) {
      // Add text before this finding
      if (finding.span_start! > lastIndex) {
        result.push(text.substring(lastIndex, finding.span_start!));
      }
      
      // Add highlighted text
      const highlightedText = text.substring(finding.span_start!, finding.span_end!);
      result.push(
        <span key={`${finding.rule_id}-${finding.span_start}`} className={`highlight ${getSeverityClass(finding.severity)}`}>
          {highlightedText}
        </span>
      );
      
      lastIndex = finding.span_end!;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      result.push(text.substring(lastIndex));
    }
    
    return result;
  };


  return (
    <div className="App">
      <header>
        <h1>Rule-Anchored Localization QA</h1>
        <p>MVP system for automated translation quality assessment.</p>
      </header>

      <main>
        <div className="evaluation-form card">
          <h2>New Evaluation</h2>
          <textarea
            placeholder="Source Text"
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
          />
          <textarea
            placeholder="Target Text"
            value={targetText}
            onChange={(e) => setTargetText(e.target.value)}
          />
          <div className="form-controls">
            <select value={locale} onChange={e => setLocale(e.target.value)}>
                <option value="zh-CN">Chinese (zh-CN)</option>
                {/* Add other locales as supported */}
            </select>
            <select value={kbVersion} onChange={e => setKbVersion(e.target.value)}>
              <option value="" disabled>Select Knowledge Base</option>
              {knowledgeBases.map(kb => (
                <option key={kb.kb_version} value={kb.kb_version}>
                  {kb.kb_version} ({kb.source_document})
                </option>
              ))}
            </select>
            <button onClick={handleEvaluate} disabled={isLoading}>
              {isLoading ? 'Evaluating...' : 'Evaluate'}
            </button>
          </div>
        </div>

        {error && <div className="error-message card">{error}</div>}

        {scoreReport && (
          <div className="results-section">
            <h2>Evaluation Report</h2>
            <div className="score-summary card">
                <div className="score-display">
                    <span>Final Score</span>
                    <span className={`score-value ${scoreReport.final_score >= 90 ? 'score-good' : 'score-bad'}`}>
                        {scoreReport.final_score.toFixed(2)}
                    </span>
                </div>
                <div className="score-details">
                    <p><strong>Job ID:</strong> {scoreReport.job_id}</p>
                    <p><strong>KB Version:</strong> {scoreReport.kb_version}</p>
                    <p><strong>Target Text:</strong></p>
                    <p className="highlighted-text-display">
                        {renderHighlightedTextWithFindings(scoreReport.target_text, scoreReport.findings)}
                    </p>
                </div>
            </div>

            <h3>Findings ({scoreReport.findings.length})</h3>
            <div className="findings-list">
              {scoreReport.findings.map((finding) => (
                <div key={finding.segment_id} className={`finding-card card ${finding.dismissed ? 'dismissed' : ''}`}>
                  <div className="finding-header">
                    <span className={`severity-badge ${getSeverityClass(finding.severity)}`}>{finding.severity}</span>
                    <span className="rule-id">{finding.rule_id}</span>
                  </div>
                  <div className="finding-body">
                    <p><strong>Justification:</strong> {finding.justification}</p>
                    {finding.highlighted_text && <p><strong>Violation:</strong> <span className="highlighted-text">{finding.highlighted_text}</span></p>}
                    <p className="citation">
                      <strong>Citation:</strong> Section {finding.citation.section_path.join('.')}
                    </p>
                  </div>
                  <div className="finding-actions">
                     <select 
                        value={finding.override_severity || finding.severity} 
                        onChange={(e) => handleOverride(finding.segment_id, 'change_severity', e.target.value as Severity)}
                        disabled={finding.dismissed}
                     >
                        <option value={Severity.MINOR}>Minor</option>
                        <option value={Severity.MAJOR}>Major</option>
                        <option value={Severity.CRITICAL}>Critical</option>
                     </select>
                     <button onClick={() => handleOverride(finding.segment_id, 'accept')} disabled={finding.dismissed}>
                        {finding.accepted ? 'Unaccept' : 'Accept'}
                     </button>
                     <button onClick={() => handleOverride(finding.segment_id, 'dismiss')} className="dismiss-btn">
                        {finding.dismissed ? 'Un-dismiss' : 'Dismiss'}
                     </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
