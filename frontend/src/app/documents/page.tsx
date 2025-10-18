'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { documentService } from '@/services/documentService';
import { Document } from '@/types/document';

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState('');

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await documentService.getDocuments();
      setDocuments(data.documents);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents');
      console.error('Error loading documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDocument = async () => {
    if (!newDocTitle.trim()) {
      alert('Please enter a document title');
      return;
    }

    try {
      setIsCreating(true);
      const newDoc = await documentService.createDocument({
        title: newDocTitle,
        content: ''
      });
      // Navigate to the new document
      router.push(`/documents/${newDoc.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create document');
      console.error('Error creating document:', err);
      setIsCreating(false);
    }
  };

  const handleDocumentClick = (documentId: string) => {
    router.push(`/documents/${documentId}`);
  };

  const handleDeleteDocument = async (documentId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }

    try {
      await documentService.deleteDocument(documentId);
      // Reload documents list
      await loadDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document');
      console.error('Error deleting document:', err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <div className="row mb-4">
        <div className="col">
          <h1>My Documents</h1>
          <p className="text-muted">Total: {total} documents</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {error}
          <button
            type="button"
            className="btn-close"
            onClick={() => setError(null)}
            aria-label="Close"
          ></button>
        </div>
      )}

      {/* Create New Document Section */}
      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title">Create New Document</h5>
          <div className="input-group">
            <input
              type="text"
              className="form-control"
              placeholder="Enter document title..."
              value={newDocTitle}
              onChange={(e) => setNewDocTitle(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleCreateDocument();
                }
              }}
              disabled={isCreating}
            />
            <button
              className="btn btn-primary"
              onClick={handleCreateDocument}
              disabled={isCreating || !newDocTitle.trim()}
            >
              {isCreating ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Creating...
                </>
              ) : (
                'Create Document'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Documents List */}
      {documents.length === 0 ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <h5 className="text-muted">No documents yet</h5>
            <p className="text-muted">Create your first document to get started!</p>
          </div>
        </div>
      ) : (
        <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
          {documents.map((doc) => (
            <div key={doc.id} className="col">
              <div className="card h-100 shadow-sm hover-shadow">
                <div className="card-body">
                  <h5
                    className="card-title text-primary"
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleDocumentClick(doc.id)}
                  >
                    {doc.title}
                  </h5>
                  <p className="card-text text-muted small">
                    {doc.content.substring(0, 100)}
                    {doc.content.length > 100 ? '...' : ''}
                  </p>
                  <div className="text-muted small mb-2">
                    <div>Created: {formatDate(doc.created_at)}</div>
                    <div>Updated: {formatDate(doc.updated_at)}</div>
                  </div>
                </div>
                <div className="card-footer bg-transparent">
                  <div className="d-flex justify-content-between">
                    <button
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => handleDocumentClick(doc.id)}
                    >
                      Open
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDocument(doc.id, doc.title);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .hover-shadow:hover {
          box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
          transition: box-shadow 0.3s ease-in-out;
        }
      `}</style>
    </div>
  );
}
