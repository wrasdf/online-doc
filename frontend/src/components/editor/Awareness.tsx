/**
 * Awareness component for displaying user presence and cursor indicators.
 *
 * Shows:
 * - Active users list
 * - Cursor indicators for each user
 * - User presence badges
 */

import React, { useEffect, useState } from 'react';
import { CollaborationManager, UserAwareness } from '@/services/collaboration';

interface AwarenessProps {
  collaborationManager: CollaborationManager | null;
  currentUserId: string;
  currentUsername: string;
}

interface ActiveUser {
  user_id: string;
  username: string;
  cursor_color: string;
  cursor_position?: number;
  selection_start?: number;
  selection_end?: number;
}

/**
 * User presence list showing all active users
 */
export function UserPresenceList({ users }: { users: ActiveUser[] }) {
  return (
    <div className="user-presence-list" data-testid="user-presence">
      <div className="d-flex align-items-center gap-2 flex-wrap">
        <small className="text-muted">Active users:</small>
        {users.length === 0 ? (
          <small className="text-muted">Just you</small>
        ) : (
          users.map((user) => (
            <div
              key={user.user_id}
              className="badge rounded-pill d-flex align-items-center gap-1"
              style={{
                backgroundColor: user.cursor_color,
                color: '#fff',
              }}
              data-testid={`user-presence`}
            >
              <span className="user-initials">
                {user.username.charAt(0).toUpperCase()}
              </span>
              <span>{user.username}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * Cursor indicator component for displaying remote user cursors
 */
export function CursorIndicator({
  user,
  position,
}: {
  user: ActiveUser;
  position: { top: number; left: number };
}) {
  return (
    <div
      className="cursor-indicator"
      data-testid="cursor-indicator"
      data-user={user.username}
      style={{
        position: 'absolute',
        top: position.top,
        left: position.left,
        zIndex: 1000,
        pointerEvents: 'none',
      }}
    >
      {/* Cursor line */}
      <div
        style={{
          width: '2px',
          height: '20px',
          backgroundColor: user.cursor_color,
        }}
      />
      {/* User label */}
      <div
        className="cursor-label"
        style={{
          position: 'absolute',
          top: '-20px',
          left: '0',
          padding: '2px 6px',
          backgroundColor: user.cursor_color,
          color: '#fff',
          borderRadius: '3px',
          fontSize: '11px',
          whiteSpace: 'nowrap',
          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        }}
      >
        {user.username}
      </div>
    </div>
  );
}

/**
 * Awareness manager component
 */
export function AwarenessManager({
  collaborationManager,
  currentUserId,
  currentUsername,
}: AwarenessProps) {
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [cursors, setCursors] = useState<Map<string, UserAwareness>>(new Map());

  useEffect(() => {
    if (!collaborationManager) {
      return;
    }

    // Setup event listeners
    const handleUserJoined = (user: {
      user_id: string;
      username: string;
      cursor_color: string;
    }) => {
      // Don't add ourselves
      if (user.user_id === currentUserId) {
        return;
      }

      setActiveUsers((prev) => {
        // Check if user already exists
        if (prev.find((u) => u.user_id === user.user_id)) {
          return prev;
        }
        return [...prev, user];
      });

      // Show notification
      showNotification(`${user.username} joined`, 'success');
    };

    const handleUserLeft = (user_id: string, username: string) => {
      setActiveUsers((prev) => prev.filter((u) => u.user_id !== user_id));

      // Remove cursor
      setCursors((prev) => {
        const newCursors = new Map(prev);
        newCursors.delete(user_id);
        return newCursors;
      });

      // Show notification
      showNotification(`${username} left`, 'info');
    };

    const handleAwarenessUpdate = (awareness: UserAwareness) => {
      // Don't track our own cursor
      if (awareness.user_id === currentUserId) {
        return;
      }

      setCursors((prev) => {
        const newCursors = new Map(prev);
        newCursors.set(awareness.user_id, awareness);
        return newCursors;
      });
    };

    // Register event handlers
    collaborationManager.onUserJoined = handleUserJoined;
    collaborationManager.onUserLeft = handleUserLeft;
    collaborationManager.onAwarenessUpdate = handleAwarenessUpdate;

    // Initialize awareness with current user info
    collaborationManager.updateAwareness({
      user_id: currentUserId,
      username: currentUsername,
      cursor_position: 0,
      cursor_color: '#000000', // Will be assigned by server
    });

    // Cleanup
    return () => {
      collaborationManager.onUserJoined = undefined;
      collaborationManager.onUserLeft = undefined;
      collaborationManager.onAwarenessUpdate = undefined;
    };
  }, [collaborationManager, currentUserId, currentUsername]);

  return (
    <>
      <UserPresenceList users={activeUsers} />
      {/* Cursor indicators would be rendered in the editor component */}
    </>
  );
}

/**
 * Connection status indicator
 */
export function ConnectionStatus({
  connected,
}: {
  connected: boolean;
}) {
  return (
    <div
      className="connection-status d-flex align-items-center gap-2"
      data-testid="connection-status"
    >
      <div
        className="status-indicator"
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: connected ? '#28a745' : '#dc3545',
        }}
      />
      <small className="text-muted">
        {connected ? 'Connected' : 'Disconnected'}
      </small>
    </div>
  );
}

/**
 * Auto-save status indicator
 */
export function SaveStatus({
  status,
}: {
  status: 'saved' | 'saving' | 'unsaved';
}) {
  const statusText = {
    saved: 'Saved',
    saving: 'Saving...',
    unsaved: 'Unsaved changes',
  };

  const statusColor = {
    saved: 'text-success',
    saving: 'text-primary',
    unsaved: 'text-warning',
  };

  return (
    <div
      className="save-status"
      data-testid="save-status"
    >
      <small className={statusColor[status]}>
        {status === 'saving' && (
          <span className="spinner-border spinner-border-sm me-2" role="status">
            <span className="visually-hidden">Saving...</span>
          </span>
        )}
        {statusText[status]}
      </small>
    </div>
  );
}

/**
 * Show a toast notification
 */
function showNotification(message: string, type: 'success' | 'info' | 'warning' | 'error') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed top-0 end-0 m-3`;
  notification.style.zIndex = '9999';
  notification.setAttribute('data-testid', 'notification');
  notification.textContent = message;

  document.body.appendChild(notification);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

/**
 * Combined awareness provider component
 */
export function AwarenessProvider({
  collaborationManager,
  currentUserId,
  currentUsername,
  connected,
  saveStatus,
}: AwarenessProps & {
  connected: boolean;
  saveStatus: 'saved' | 'saving' | 'unsaved';
}) {
  return (
    <div className="awareness-provider">
      {/* Status bar */}
      <div className="d-flex align-items-center justify-content-between p-2 border-bottom">
        <AwarenessManager
          collaborationManager={collaborationManager}
          currentUserId={currentUserId}
          currentUsername={currentUsername}
        />
        <div className="d-flex align-items-center gap-3">
          <SaveStatus status={saveStatus} />
          <ConnectionStatus connected={connected} />
        </div>
      </div>
    </div>
  );
}

export default AwarenessProvider;
