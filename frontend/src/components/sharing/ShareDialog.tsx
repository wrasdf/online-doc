'use client';

import React, { useState, useEffect } from 'react';
import apiClient from '@/services/api';
import { CollaboratorInfo, ShareDocumentRequest, ShareResponse, CollaboratorsResponse } from '@/types/sharing';

interface ShareDialogProps {
  documentId: string;
  isOpen: boolean;
  onClose: () => void;
  onShare?: (collaborators: CollaboratorInfo[]) => void;
}

const ShareDialog: React.FC<ShareDialogProps> = ({ documentId, isOpen, onClose, onShare }) => {
  const [collaborators, setCollaborators] = useState<CollaboratorInfo[]>([]);
  const [emailInput, setEmailInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch existing collaborators when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchCollaborators();
    }
  }, [isOpen, documentId]);

  const fetchCollaborators = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<CollaboratorsResponse>(
        `/documents/${documentId}/collaborators`
      );
      setCollaborators(response.data.collaborators);
    } catch (err: any) {
      console.error('Failed to fetch collaborators:', err);
      setError(err.response?.data?.detail || 'Failed to load collaborators');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!emailInput.trim()) {
      setError('Please enter an email address');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      // First, search for user by email
      const searchResponse = await apiClient.get(`/users/search`, {
        params: { email: emailInput.trim() }
      });

      if (!searchResponse.data || searchResponse.data.length === 0) {
        setError('User not found with that email address');
        setLoading(false);
        return;
      }

      const userId = searchResponse.data[0].id;

      // Share the document with the user
      const shareRequest: ShareDocumentRequest = {
        user_ids: [userId]
      };

      const response = await apiClient.post<ShareResponse>(
        `/documents/${documentId}/share`,
        shareRequest
      );

      setSuccessMessage(`Successfully shared with ${emailInput}`);
      setEmailInput('');
      setCollaborators(response.data.shared_with);

      if (onShare) {
        onShare(response.data.shared_with);
      }
    } catch (err: any) {
      console.error('Failed to share document:', err);
      setError(err.response?.data?.detail || 'Failed to share document');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveCollaborator = async (userId: string) => {
    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      await apiClient.delete(`/documents/${documentId}/share/${userId}`);

      setSuccessMessage('Collaborator removed successfully');
      await fetchCollaborators();
    } catch (err: any) {
      console.error('Failed to remove collaborator:', err);
      setError(err.response?.data?.detail || 'Failed to remove collaborator');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleShare();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Bootstrap Modal Backdrop */}
      <div
        className="modal-backdrop fade show"
        onClick={onClose}
        style={{ zIndex: 1040 }}
      />

      {/* Bootstrap Modal */}
      <div
        className="modal fade show d-block"
        tabIndex={-1}
        role="dialog"
        style={{ zIndex: 1050 }}
      >
        <div className="modal-dialog modal-dialog-centered" role="document">
          <div className="modal-content">
            {/* Modal Header */}
            <div className="modal-header">
              <h5 className="modal-title">Share Document</h5>
              <button
                type="button"
                className="btn-close"
                onClick={onClose}
                aria-label="Close"
                disabled={loading}
              />
            </div>

            {/* Modal Body */}
            <div className="modal-body">
              {/* Error Alert */}
              {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                  {error}
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setError(null)}
                    aria-label="Close"
                  />
                </div>
              )}

              {/* Success Alert */}
              {successMessage && (
                <div className="alert alert-success alert-dismissible fade show" role="alert">
                  {successMessage}
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setSuccessMessage(null)}
                    aria-label="Close"
                  />
                </div>
              )}

              {/* Share Input */}
              <div className="mb-4">
                <label htmlFor="emailInput" className="form-label">
                  Add collaborator by email
                </label>
                <div className="input-group">
                  <input
                    type="email"
                    className="form-control"
                    id="emailInput"
                    placeholder="user@example.com"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                  />
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={handleShare}
                    disabled={loading || !emailInput.trim()}
                  >
                    {loading ? 'Sharing...' : 'Share'}
                  </button>
                </div>
                <div className="form-text">
                  Enter the email address of the user you want to share this document with.
                </div>
              </div>

              {/* Collaborators List */}
              <div>
                <h6 className="mb-3">Current Collaborators</h6>
                {loading && collaborators.length === 0 ? (
                  <div className="text-center py-3">
                    <div className="spinner-border spinner-border-sm text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                ) : collaborators.length === 0 ? (
                  <p className="text-muted text-center py-3">
                    No collaborators yet. Share this document to start collaborating!
                  </p>
                ) : (
                  <ul className="list-group">
                    {collaborators.map((collaborator) => (
                      <li
                        key={collaborator.user_id}
                        className="list-group-item d-flex justify-content-between align-items-center"
                      >
                        <div>
                          <strong>{collaborator.username}</strong>
                          <br />
                          <small className="text-muted">{collaborator.email}</small>
                          <br />
                          <span
                            className={`badge ${
                              collaborator.access_type === 'owner'
                                ? 'bg-primary'
                                : 'bg-secondary'
                            }`}
                          >
                            {collaborator.access_type}
                          </span>
                        </div>
                        {collaborator.access_type !== 'owner' && (
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleRemoveCollaborator(collaborator.user_id)}
                            disabled={loading}
                          >
                            Remove
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={loading}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ShareDialog;
