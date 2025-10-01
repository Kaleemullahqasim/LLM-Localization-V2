import { useState, useEffect } from 'react';
import axios from 'axios';

interface KnowledgeBase {
  kb_version: string;
  locale: string;
  rule_count: number;
  source_document: string;
  created_at: string;
}

const styles = {
  container: {
    maxWidth: '1600px',
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
    outline: 'none'
  } as React.CSSProperties,
  button: {
    padding: '0.875rem 1.5rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    fontSize: '0.9375rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 2px 4px rgba(102, 126, 234, 0.2)'
  } as React.CSSProperties
};

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'upload' | 'kbs' | 'tests'>('upload');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLocale, setUploadLocale] = useState('zh-CN');
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/knowledge-bases');
      setKnowledgeBases(response.data.knowledge_bases);
    } catch (err) {
      console.error('Failed to fetch KBs:', err);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage({type: 'error', text: 'Please select a file'});
      return;
    }

    setIsUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('locale', uploadLocale);

      const response = await axios.post('http://localhost:8000/api/upload-document', formData);
      setMessage({type: 'success', text: `Successfully created KB with ${response.data.rule_count} rules!`});
      setSelectedFile(null);
      fetchKnowledgeBases();
    } catch (err: any) {
      setMessage({type: 'error', text: err.response?.data?.detail || 'Upload failed'});
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteKB = async (kbVersion: string) => {
    if (!confirm(`Delete KB ${kbVersion}?`)) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/knowledge-bases/${kbVersion}`);
      setMessage({type: 'success', text: 'KB deleted successfully'});
      fetchKnowledgeBases();
    } catch (err: any) {
      setMessage({type: 'error', text: 'Failed to delete KB'});
    }
  };

  return (
    <div style={styles.container}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', color: '#1e293b', marginBottom: '0.5rem' }}>
          Admin Dashboard
        </h2>
        <p style={{ color: '#64748b', fontSize: '1rem' }}>
          Manage style guides, knowledge bases, and system configuration
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', borderBottom: '2px solid #f1f5f9', paddingBottom: '0' }}>
        {[
          { id: 'upload', label: 'Upload Guide', icon: '📤' },
          { id: 'kbs', label: 'Knowledge Bases', icon: '📚' },
          { id: 'tests', label: 'All Tests', icon: '📊' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              padding: '0.875rem 1.5rem',
              border: 'none',
              background: 'transparent',
              color: activeTab === tab.id ? '#667eea' : '#64748b',
              fontWeight: activeTab === tab.id ? '600' : '500',
              cursor: 'pointer',
              borderBottom: activeTab === tab.id ? '2px solid #667eea' : '2px solid transparent',
              marginBottom: '-2px',
              transition: 'all 0.2s',
              fontSize: '0.9375rem'
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.color = '#475569';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.color = '#64748b';
              }
            }}
          >
            <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {message && (
        <div style={{
          padding: '1rem 1.25rem',
          borderRadius: '0.5rem',
          marginBottom: '1.5rem',
          background: message.type === 'success' ? '#f0fdf4' : '#fef2f2',
          color: message.type === 'success' ? '#166534' : '#dc2626',
          border: `1px solid ${message.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
          fontSize: '0.9375rem'
        }}>
          {message.text}
        </div>
      )}

      {/* Upload Guide Tab */}
      {activeTab === 'upload' && (
        <div style={styles.card}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem', color: '#1e293b' }}>
            Upload Style Guide
          </h3>
          <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: '0.9375rem' }}>
            Upload a style guide document to create a new knowledge base with extracted rules
          </p>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              padding: '3rem',
              border: selectedFile ? '2px solid #667eea' : '2px dashed #cbd5e1',
              borderRadius: '0.75rem',
              textAlign: 'center',
              cursor: 'pointer',
              background: selectedFile ? '#f5f7ff' : '#fafbfc',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#667eea';
              e.currentTarget.style.background = '#f5f7ff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = selectedFile ? '#667eea' : '#cbd5e1';
              e.currentTarget.style.background = selectedFile ? '#f5f7ff' : '#fafbfc';
            }}>
              <input
                type="file"
                accept=".docx,.pdf,.html,.md"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
              />
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
              <div style={{ fontWeight: '600', color: '#1e293b', marginBottom: '0.5rem', fontSize: '1rem' }}>
                {selectedFile ? selectedFile.name : 'Click to select file or drag and drop'}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                DOCX, PDF, HTML, or Markdown (Max 50MB)
              </div>
            </label>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#334155', fontSize: '0.875rem' }}>
              Target Locale
            </label>
            <select
              value={uploadLocale}
              onChange={(e) => setUploadLocale(e.target.value)}
              style={styles.input}
              onFocus={(e: any) => {
                e.target.style.borderColor = '#667eea';
                e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
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
              <option value="es-ES">Spanish</option>
              <option value="fr-FR">French</option>
              <option value="de-DE">German</option>
            </select>
          </div>

          <button
            onClick={handleUpload}
            disabled={isUploading || !selectedFile}
            style={{
              ...styles.button,
              width: '100%',
              opacity: isUploading || !selectedFile ? 0.5 : 1,
              cursor: isUploading || !selectedFile ? 'not-allowed' : 'pointer'
            }}
            onMouseEnter={(e) => {
              if (!isUploading && selectedFile) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.3)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(102, 126, 234, 0.2)';
            }}
          >
            {isUploading ? '🔄 Processing...' : '🚀 Create Knowledge Base'}
          </button>
        </div>
      )}

      {/* Knowledge Bases Tab */}
      {activeTab === 'kbs' && (
        <div style={styles.card}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#1e293b' }}>
            Knowledge Bases ({knowledgeBases.length})
          </h3>

          {knowledgeBases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📚</div>
              <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#475569', marginBottom: '0.5rem' }}>
                No knowledge bases yet
              </h4>
              <p style={{ fontSize: '0.9375rem' }}>
                Upload a style guide to get started
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {knowledgeBases.map((kb) => (
                <div key={kb.kb_version} style={{
                  padding: '1.5rem',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.75rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s',
                  background: 'white'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#cbd5e1';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e2e8f0';
                  e.currentTarget.style.boxShadow = 'none';
                }}>
                  <div>
                    <h4 style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#1e293b', fontSize: '1rem' }}>
                      {kb.source_document}
                    </h4>
                    <div style={{ fontSize: '0.875rem', color: '#64748b', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                      <span style={{ background: '#f1f5f9', padding: '0.25rem 0.75rem', borderRadius: '0.25rem' }}>
                        {kb.kb_version}
                      </span>
                      <span>{kb.rule_count} rules</span>
                      <span>{kb.locale}</span>
                      <span>{new Date(kb.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteKB(kb.kb_version)}
                    style={{
                      padding: '0.625rem 1.25rem',
                      background: '#fef2f2',
                      color: '#dc2626',
                      border: '1px solid #fecaca',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      fontWeight: '500',
                      fontSize: '0.875rem',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#fee2e2';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#fef2f2';
                    }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* All Tests Tab */}
      {activeTab === 'tests' && (
        <div style={styles.card}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#1e293b' }}>
            All Test Submissions
          </h3>
          <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📊</div>
            <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#475569', marginBottom: '0.5rem' }}>
              Test history coming soon
            </h4>
            <p style={{ fontSize: '0.9375rem' }}>
              All translations submitted by test takers will appear here
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
