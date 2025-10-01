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
  model_prompt_version: string;
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

// Tab types
type TabType = 'evaluate' | 'upload' | 'kbs' | 'help';


function App() {
  // Main state
  const [activeTab, setActiveTab] = useState<TabType>('evaluate');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Evaluation state
  const [sourceText, setSourceText] = useState('Welcome to Shopify!');
  const [targetText, setTargetText] = useState('欢迎使用Shopify!');
  const [locale, setLocale] = useState('zh-CN');
  const [kbVersion, setKbVersion] = useState('');
  const [scoreReport, setScoreReport] = useState<ScoreReport | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  
  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLocale, setUploadLocale] = useState('zh-CN');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const handleEvaluate = async () => {
    if (!kbVersion) {
      setError('Please select a Knowledge Base.');
      return;
    }
    setIsEvaluating(true);
    setError(null);
    setScoreReport(null);

    try {
      const response = await axios.post<ScoreReport>('http://localhost:8000/api/evaluate', {
        source_text: sourceText,
        target_text: targetText,
        locale: locale,
        kb_version: kbVersion,
      });
      setScoreReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An unknown error occurred during evaluation.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('locale', uploadLocale);

      const response = await axios.post('http://localhost:8000/api/upload-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      // Refresh knowledge bases
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during file upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const fetchKnowledgeBases = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/knowledge-bases');
      setKnowledgeBases(response.data.knowledge_bases);
      // Auto-select the first KB if available
      if (response.data.knowledge_bases.length > 0 && !kbVersion) {
        setKbVersion(response.data.knowledge_bases[0].kb_version);
      }
    } catch (err) {
      console.error('Failed to fetch knowledge bases:', err);
    }
  };

  const handleDeleteKB = async (kbVersionToDelete: string) => {
    if (!confirm(`Are you sure you want to delete knowledge base ${kbVersionToDelete}? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`http://localhost:8000/api/knowledge-bases/${kbVersionToDelete}`);
      // Refresh knowledge bases
      await fetchKnowledgeBases();
      // Clear selected KB if it was deleted
      if (kbVersion === kbVersionToDelete) {
        setKbVersion('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete knowledge base');
    }
  };

  const handleOverride = async (findingId: string, action: string, newSeverity?: Severity) => {
    if (!scoreReport) return;
    
    try {
      // Call backend API to process override
      const response = await axios.post('http://localhost:8000/api/review/override', {
        finding_id: findingId,
        action: action,
        new_severity: newSeverity,
        reason: `User ${action} via UI`,
        reviewer: 'current-user'
      });
      
      console.log('Override processed:', response.data);
      
      // Reload the evaluation to get updated scores
      const evalResponse = await axios.get(`http://localhost:8000/api/evaluation/${scoreReport.job_id}`);
      setScoreReport(evalResponse.data);
      
    } catch (err: any) {
      console.error('Override failed:', err);
      setError(err.response?.data?.detail || 'Failed to process override');
      
      // Fallback: update UI locally if backend fails
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
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <h1>Rule-Anchored Localization QA</h1>
            <p>AI-powered translation quality assessment with explainable scoring</p>
          </div>
          <div className="status-section">
            <div className="status-item">
              <span className="status-label">Knowledge Bases:</span>
              <span className="status-value">{knowledgeBases.length}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Total Rules:</span>
              <span className="status-value">
                {knowledgeBases.reduce((sum, kb) => sum + kb.rule_count, 0)}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'evaluate' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluate')}
        >
          📊 Evaluate Translation
        </button>
        <button 
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📤 Upload Style Guide
        </button>
        <button 
          className={`tab-button ${activeTab === 'kbs' ? 'active' : ''}`}
          onClick={() => setActiveTab('kbs')}
        >
          📚 Knowledge Bases
        </button>
        <button 
          className={`tab-button ${activeTab === 'help' ? 'active' : ''}`}
          onClick={() => setActiveTab('help')}
        >
          ❓ How It Works
        </button>
      </nav>

      {/* Error Message */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className="error-close">×</button>
        </div>
      )}

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'evaluate' && (
          <div className="tab-content">
            <div className="section-card">
              <h2>Translation Evaluation</h2>
              <div className="form-grid">
                <div className="form-group">
                  <label>Source Text (English)</label>
                  <textarea
                    value={sourceText}
                    onChange={(e) => setSourceText(e.target.value)}
                    placeholder="Enter the original text to be translated..."
                    rows={4}
                  />
                </div>
                <div className="form-group">
                  <label>Target Text (Translation)</label>
                  <textarea
                    value={targetText}
                    onChange={(e) => setTargetText(e.target.value)}
                    placeholder="Enter the translation to be evaluated..."
                    rows={4}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Target Locale</label>
                    <select value={locale} onChange={e => setLocale(e.target.value)}>
                      <option value="zh-CN">Chinese (Simplified)</option>
                      <option value="zh-TW">Chinese (Traditional)</option>
                      <option value="ja-JP">Japanese</option>
                      <option value="ko-KR">Korean</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Knowledge Base</label>
                    <select value={kbVersion} onChange={e => setKbVersion(e.target.value)}>
                      <option value="">Select a knowledge base...</option>
                      {knowledgeBases.map(kb => (
                        <option key={kb.kb_version} value={kb.kb_version}>
                          {kb.source_document} ({kb.rule_count} rules)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <button 
                  onClick={handleEvaluate} 
                  disabled={isEvaluating || !kbVersion}
                  className="primary-button"
                >
                  {isEvaluating ? '🔄 Evaluating...' : '🚀 Evaluate Translation'}
                </button>
              </div>
            </div>

            {scoreReport && (
              <>
                <div className="section-card score-card">
                  <h2>Evaluation Results</h2>
                  <div className="score-overview">
                    <div className="score-circle">
                      <div className={`score-value ${scoreReport.final_score >= 90 ? 'excellent' : scoreReport.final_score >= 80 ? 'good' : 'needs-work'}`}>
                        {scoreReport.final_score}
                      </div>
                      <div className="score-label">Final Score</div>
                    </div>
                    <div className="score-details">
                      <div className="detail-item">
                        <span className="label">Job ID:</span>
                        <span className="value">{scoreReport.job_id.substring(0, 8)}...</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">KB Version:</span>
                        <span className="value">{scoreReport.kb_version}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">Model Version:</span>
                        <span className="value">{scoreReport.model_prompt_version}</span>
                      </div>
                      <div className="detail-item">
                        <span className="label">Findings:</span>
                        <span className="value">{scoreReport.findings.length} issues detected</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="score-breakdown">
                    <h3>Score Breakdown by Category</h3>
                    <div className="breakdown-grid">
                      {Object.entries(scoreReport.by_macro).map(([category, breakdown]) => (
                        <div key={category} className="breakdown-item">
                          <div className="category-name">{category}</div>
                          <div className="category-penalty">-{breakdown.penalty} pts</div>
                          <div className="category-count">{breakdown.count} issues</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="highlighted-text-section">
                    <h3>Translation with Highlights</h3>
                    <div className="highlighted-text-display">
                      {renderHighlightedTextWithFindings(scoreReport.target_text, scoreReport.findings)}
                    </div>
                  </div>
                </div>

                <div className="section-card">
                  <h2>Detailed Findings ({scoreReport.findings.length})</h2>
                  <div className="findings-grid">
                    {scoreReport.findings.map((finding, index) => (
                      <div key={finding.segment_id} className={`finding-card ${finding.dismissed ? 'dismissed' : ''}`}>
                        <div className="finding-header">
                          <div className="finding-number">#{index + 1}</div>
                          <div className={`severity-badge ${getSeverityClass(finding.severity)}`}>
                            {finding.severity}
                          </div>
                          <div className="rule-id">{finding.rule_id}</div>
                          <div className="penalty">-{finding.penalty} pts</div>
                        </div>
                        
                        <div className="finding-content">
                          <div className="justification">
                            <strong>Issue:</strong> {finding.justification}
                          </div>
                          
                          {finding.highlighted_text && (
                            <div className="violation-text">
                              <strong>Problematic text:</strong> 
                              <span className="highlighted-snippet">{finding.highlighted_text}</span>
                            </div>
                          )}
                          
                          <div className="citation">
                            <strong>Rule source:</strong> Section {finding.citation.section_path.join('.')}
                            <span className="detection-type">
                              {finding.deterministic ? '🤖 Automatic' : '🧠 AI-detected'}
                            </span>
                          </div>
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
                          <button 
                            onClick={() => handleOverride(finding.segment_id, 'accept')} 
                            disabled={finding.dismissed}
                            className="action-button accept"
                          >
                            {finding.accepted ? '✅ Accepted' : '✓ Accept'}
                          </button>
                          <button 
                            onClick={() => handleOverride(finding.segment_id, 'dismiss')} 
                            className="action-button dismiss"
                          >
                            {finding.dismissed ? '↩️ Restore' : '🗑️ Dismiss'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="tab-content">
            <div className="section-card">
              <h2>Upload Style Guide</h2>
              <p>Upload a style guide document to create a new knowledge base with extracted rules.</p>
              
              <div className="upload-section">
                <div className="file-upload-area">
                  <input
                    type="file"
                    id="file-input"
                    accept=".docx,.pdf,.html,.htm,.md,.markdown"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="file-input"
                  />
                  <label htmlFor="file-input" className="file-upload-label">
                    <div className="upload-icon">📄</div>
                    <div className="upload-text">
                      {selectedFile ? selectedFile.name : 'Click to select or drag & drop'}
                    </div>
                    <div className="upload-hint">
                      Supports: DOCX, PDF, HTML, Markdown
                    </div>
                  </label>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Target Locale</label>
                    <select value={uploadLocale} onChange={e => setUploadLocale(e.target.value)}>
                      <option value="zh-CN">Chinese (Simplified)</option>
                      <option value="zh-TW">Chinese (Traditional)</option>
                      <option value="ja-JP">Japanese</option>
                      <option value="ko-KR">Korean</option>
                    </select>
                  </div>
                </div>

                <button 
                  onClick={handleFileUpload} 
                  disabled={isUploading || !selectedFile}
                  className="primary-button"
                >
                  {isUploading ? '🔄 Processing...' : '🚀 Create Knowledge Base'}
                </button>
              </div>

              {uploadResult && (
                <div className="upload-result">
                  <h3>✅ Upload Successful!</h3>
                  <div className="result-details">
                    <p><strong>KB Version:</strong> {uploadResult.kb_version}</p>
                    <p><strong>Rules Extracted:</strong> {uploadResult.rule_count}</p>
                    <p><strong>Source File:</strong> {uploadResult.filename}</p>
                    <p><strong>Locale:</strong> {uploadResult.locale}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'kbs' && (
          <div className="tab-content">
            <div className="section-card">
              <h2>Knowledge Bases</h2>
              <p>Manage your uploaded style guides and their extracted rules.</p>
              
              <div className="kb-grid">
                {knowledgeBases.map((kb) => (
                  <div key={kb.kb_version} className="kb-card">
                    <div className="kb-header">
                      <h3>{kb.source_document}</h3>
                      <span className="kb-version">{kb.kb_version}</span>
                    </div>
                    <div className="kb-details">
                      <div className="kb-stat">
                        <span className="stat-label">Rules:</span>
                        <span className="stat-value">{kb.rule_count}</span>
                      </div>
                      <div className="kb-stat">
                        <span className="stat-label">Locale:</span>
                        <span className="stat-value">{kb.locale}</span>
                      </div>
                      <div className="kb-stat">
                        <span className="stat-label">Created:</span>
                        <span className="stat-value">{new Date(kb.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="kb-actions">
                      <button 
                        onClick={() => {
                          setKbVersion(kb.kb_version);
                          setActiveTab('evaluate');
                        }}
                        className="use-kb-button"
                      >
                        Use for Evaluation
                      </button>
                      <button 
                        onClick={() => handleDeleteKB(kb.kb_version)}
                        className="delete-kb-button"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {knowledgeBases.length === 0 && (
                <div className="empty-state">
                  <div className="empty-icon">📚</div>
                  <h3>No Knowledge Bases Found</h3>
                  <p>Upload a style guide to create your first knowledge base.</p>
                  <button 
                    onClick={() => setActiveTab('upload')}
                    className="primary-button"
                  >
                    Upload Style Guide
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'help' && (
          <div className="tab-content">
            <div className="section-card">
              <h2>How It Works</h2>
              
              <div className="help-section">
                <h3>🧠 AI-Powered Rule Extraction</h3>
                <p>The system uses Large Language Models (LLMs) to automatically extract translation quality rules from your style guides:</p>
                <ul>
                  <li><strong>Document Processing:</strong> Converts DOCX/PDF/HTML/MD files to structured text</li>
                  <li><strong>Rule Mining:</strong> Identifies rule cues like "must", "never", "should", "avoid"</li>
                  <li><strong>LLM Normalization:</strong> Uses structured output to create atomic, testable rules</li>
                  <li><strong>Classification:</strong> Automatically categorizes rules by type (Punctuation, Terminology, etc.)</li>
                </ul>
              </div>

              <div className="help-section">
                <h3>🔍 Hybrid Evaluation Engine</h3>
                <p>Translation evaluation combines multiple approaches for comprehensive quality assessment:</p>
                <ul>
                  <li><strong>Deterministic Validators:</strong> Fast regex-based checks for punctuation, placeholders, dates</li>
                  <li><strong>Semantic Search:</strong> Vector embeddings find relevant rules for the translation context</li>
                  <li><strong>LLM Analysis:</strong> AI evaluates translations against retrieved rules with explanations</li>
                  <li><strong>Scoring Engine:</strong> Calculates weighted scores with severity multipliers and category caps</li>
                </ul>
              </div>

              <div className="help-section">
                <h3>📊 Explainable Scoring</h3>
                <p>Every deduction is tied to a specific rule with full transparency:</p>
                <ul>
                  <li><strong>Rule Citations:</strong> Each finding references the exact section in your style guide</li>
                  <li><strong>Severity Levels:</strong> Minor (1x), Major (2x), Critical (3x) multipliers</li>
                  <li><strong>Category Weights:</strong> Different rule types have different impact on final score</li>
                  <li><strong>Human Override:</strong> Reviewers can adjust severity or dismiss findings</li>
                </ul>
              </div>

              <div className="help-section">
                <h3>🔧 Technical Architecture</h3>
                <p>The system integrates with LM Studio for local AI processing:</p>
                <ul>
                  <li><strong>Chat Model:</strong> For rule extraction and translation evaluation</li>
                  <li><strong>Embedding Model:</strong> For semantic similarity and rule retrieval</li>
                  <li><strong>Structured Output:</strong> JSON schemas ensure consistent AI responses</li>
                  <li><strong>Version Control:</strong> All evaluations are reproducible with version stamps</li>
                </ul>
              </div>

              <div className="help-section">
                <h3>🚀 Getting Started</h3>
                <ol>
                  <li>Ensure LM Studio is running with the required models</li>
                  <li>Upload a style guide document (DOCX, PDF, HTML, or Markdown)</li>
                  <li>Wait for the system to extract rules and create a knowledge base</li>
                  <li>Evaluate translations using the created knowledge base</li>
                  <li>Review findings and override AI decisions as needed</li>
                </ol>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
