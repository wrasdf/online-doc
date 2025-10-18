'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { documentService } from '@/services/documentService';
import { Document } from '@/types/document';
import CodeMirrorEditor from '@/components/editor/CodeMirrorEditor';

export default function DocumentEditPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState('');

  // Auto-save timer
  const [autoSaveTimer, setAutoSaveTimer] = useState<NodeJS.Timeout | null>(null);

  // Load document on mount
  useEffect(() => {
    if (documentId) {
      loadDocument();
    }
  }, [documentId]);

  // Cleanup auto-save timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }
    };
  }, [autoSaveTimer]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      setError(null);
      const doc = await documentService.getDocument(documentId);
      setDocument(doc);
      setTitleValue(doc.title);
      setLastSaved(new Date(doc.updated_at));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load document');
      console.error('Error loading document:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveDocument = async () => {
    if (!document) return;

    try {
      setSaving(true);
      setError(null);

      const updated = await documentService.updateDocument(documentId, {
        title: titleValue,
        content: document.content
      });

      setDocument(updated);
      setLastSaved(new Date(updated.updated_at));
      setHasUnsavedChanges(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save document');
      console.error('Error saving document:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleContentChange = (newContent: string) => {
    if (!document) return;

    setDocument({
      ...document,
      content: newContent
    });
    setHasUnsavedChanges(true);

    // Clear existing timer
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }

    // Set new auto-save timer for 15 seconds
    const timer = setTimeout(() => {
      saveDocument();
    }, 15000);

    setAutoSaveTimer(timer);
  };

  const handleTitleChange = async () => {
    if (!document || titleValue === document.title) {
      setEditingTitle(false);
      return;
    }

    if (!titleValue.trim()) {
      alert('Title cannot be empty');
      setTitleValue(document.title);
      setEditingTitle(false);
      return;
    }

    try {
      const updated = await documentService.updateDocument(documentId, {
        title: titleValue
      });
      setDocument(updated);
      setEditingTitle(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update title');
      console.error('Error updating title:', err);
    }
  };

  const handleDelete = async () => {
    if (!document) return;

    if (!confirm(`Are you sure you want to delete "${document.title}"?`)) {
      return;
    }

    try {
      await documentService.deleteDocument(documentId);
      router.push('/documents');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document');
      console.error('Error deleting document:', err);
    }
  };

  const formatLastSaved = () => {
    if (!lastSaved) return 'Not saved';
    const now = new Date();
    const diff = now.getTime() - lastSaved.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);

    if (seconds < 5) return 'Just now';
    if (seconds < 60) return `${seconds} seconds ago`;
    if (minutes === 1) return '1 minute ago';
    if (minutes < 60) return `${minutes} minutes ago`;
    return lastSaved.toLocaleString();
  };

  if (loading) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading document...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="container mt-5">
        <div className="alert alert-warning">
          Document not found
          <button
            className="btn btn-link"
            onClick={() => router.push('/documents')}
          >
            Back to documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid" style={{ height: 'calc(100vh - 100px)' }}>
      {/* Header */}
      <div className="row border-bottom bg-light py-3">
        <div className="col">
          <div className="d-flex align-items-center justify-content-between">
            {/* Title Section */}
            <div className="d-flex align-items-center flex-grow-1">
              <button
                className="btn btn-sm btn-outline-secondary me-3"
                onClick={() => router.push('/documents')}
                title="Back to documents"
              >
                ← Back
              </button>
              {editingTitle ? (
                <div className="input-group" style={{ maxWidth: '500px' }}>
                  <input
                    type="text"
                    className="form-control"
                    value={titleValue}
                    onChange={(e) => setTitleValue(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleTitleChange();
                      }
                    }}
                    onBlur={handleTitleChange}
                    autoFocus
                  />
                </div>
              ) : (
                <h4
                  className="mb-0"
                  onClick={() => setEditingTitle(true)}
                  style={{ cursor: 'pointer' }}
                  title="Click to edit title"
                >
                  {document.title}
                </h4>
              )}
            </div>

            {/* Actions Section */}
            <div className="d-flex align-items-center gap-3">
              {/* Save Status */}
              <div className="text-muted small">
                {saving ? (
                  <span>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Saving...
                  </span>
                ) : hasUnsavedChanges ? (
                  <span className="text-warning">Unsaved changes</span>
                ) : (
                  <span>Saved {formatLastSaved()}</span>
                )}
              </div>

              {/* Save Button */}
              <button
                className="btn btn-primary btn-sm"
                onClick={saveDocument}
                disabled={saving || !hasUnsavedChanges}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>

              {/* Delete Button */}
              <button
                className="btn btn-outline-danger btn-sm"
                onClick={handleDelete}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="row mt-3">
          <div className="col">
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
                aria-label="Close"
              ></button>
            </div>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="row mt-3" style={{ height: 'calc(100% - 100px)' }}>
        <div className="col">
          <CodeMirrorEditor
            value={document.content}
            onChange={handleContentChange}
            onSave={saveDocument}
            placeholder="Start typing your document..."
            className="h-100"
          />
        </div>
      </div>
    </div>
  );
}
