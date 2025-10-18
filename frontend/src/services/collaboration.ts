/**
 * Collaboration service for real-time document editing using Yjs and WebSocket.
 *
 * This service integrates:
 * - Yjs CRDT for conflict-free collaborative editing
 * - WebSocket connection to backend
 * - CodeMirror 6 editor binding
 * - Awareness for cursor tracking
 */

import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';
import { Awareness } from 'y-protocols/awareness';

/**
 * User awareness information for cursor tracking
 */
export interface UserAwareness {
  user_id: string;
  username: string;
  cursor_position: number;
  cursor_color: string;
  selection_start?: number;
  selection_end?: number;
}

/**
 * WebSocket message types
 */
export enum MessageType {
  SYNC_STEP1 = 'sync_step1',
  SYNC_STEP2 = 'sync_step2',
  SYNC_UPDATE = 'sync_update',
  AWARENESS_UPDATE = 'awareness_update',
  USER_JOINED = 'user_joined',
  USER_LEFT = 'user_left',
  ERROR = 'error',
  PING = 'ping',
  PONG = 'pong',
  SERVER_SHUTDOWN = 'server_shutdown',
}

/**
 * WebSocket message structure
 */
export interface WebSocketMessage {
  type: MessageType;
  document_id?: string;
  update?: string; // Base64 encoded Yjs update
  state?: string; // Base64 encoded Yjs state
  version?: number;
  user_id?: string;
  username?: string;
  awareness?: UserAwareness;
  user?: {
    user_id: string;
    username: string;
    cursor_color: string;
  };
  timestamp?: string;
  error?: string;
  message?: string;
  code?: number;
  reconnect?: boolean;
}

/**
 * Collaboration manager for a single document
 */
export class CollaborationManager {
  private yDoc: Y.Doc;
  private yText: Y.Text;
  private websocket: WebSocket | null = null;
  private awareness: Awareness | null = null;
  private documentId: string;
  private token: string;
  private wsUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnected = false;
  private messageQueue: WebSocketMessage[] = [];

  // Event callbacks
  public onConnect?: () => void;
  public onDisconnect?: () => void;
  public onError?: (error: string) => void;
  public onUserJoined?: (user: { user_id: string; username: string; cursor_color: string }) => void;
  public onUserLeft?: (user_id: string, username: string) => void;
  public onAwarenessUpdate?: (awareness: UserAwareness) => void;

  constructor(documentId: string, token: string, wsUrl?: string) {
    this.documentId = documentId;
    this.token = token;
    this.wsUrl = wsUrl || process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

    // Initialize Yjs document
    this.yDoc = new Y.Doc();
    this.yText = this.yDoc.getText('content');

    // Initialize awareness
    this.awareness = new Awareness(this.yDoc);

    // Setup Yjs observers
    this.setupYjsObservers();
  }

  /**
   * Setup Yjs observers for updates
   */
  private setupYjsObservers() {
    // Listen for local document updates to send to server
    this.yDoc.on('update', (update: Uint8Array, origin: any) => {
      // Only send updates if they originated locally (not from server)
      if (origin !== 'server' && this.isConnected) {
        const base64Update = this.arrayBufferToBase64(update);
        this.sendMessage({
          type: MessageType.SYNC_UPDATE,
          document_id: this.documentId,
          update: base64Update,
        });
      }
    });

    // Listen for awareness changes
    if (this.awareness) {
      this.awareness.on('change', () => {
        if (this.isConnected && this.awareness) {
          const localState = this.awareness.getLocalState();
          if (localState) {
            this.sendMessage({
              type: MessageType.AWARENESS_UPDATE,
              document_id: this.documentId,
              awareness: localState as UserAwareness,
            });
          }
        }
      });
    }
  }

  /**
   * Connect to WebSocket server
   */
  public async connect(): Promise<void> {
    const url = `${this.wsUrl}/documents/${this.documentId}?token=${this.token}`;

    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(url);

        this.websocket.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;

          // Send queued messages
          this.flushMessageQueue();

          // Request initial document state
          this.sendMessage({
            type: MessageType.SYNC_STEP1,
            document_id: this.documentId,
          });

          if (this.onConnect) {
            this.onConnect();
          }

          resolve();
        };

        this.websocket.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (this.onError) {
            this.onError('WebSocket connection error');
          }
          reject(error);
        };

        this.websocket.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnected = false;

          if (this.onDisconnect) {
            this.onDisconnect();
          }

          // Attempt reconnection if not a normal closure
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string) {
    try {
      const message: WebSocketMessage = JSON.parse(data);

      switch (message.type) {
        case MessageType.SYNC_STEP2:
          // Apply initial document state
          if (message.state) {
            const stateArray = this.base64ToArrayBuffer(message.state);
            Y.applyUpdate(this.yDoc, stateArray, 'server');
          }
          break;

        case MessageType.SYNC_UPDATE:
          // Apply document update from another user
          if (message.update) {
            const updateArray = this.base64ToArrayBuffer(message.update);
            Y.applyUpdate(this.yDoc, updateArray, 'server');
          }
          break;

        case MessageType.AWARENESS_UPDATE:
          // Update awareness with other user's cursor position
          if (message.awareness && this.onAwarenessUpdate) {
            this.onAwarenessUpdate(message.awareness);
          }
          break;

        case MessageType.USER_JOINED:
          // Notify that a user joined
          if (message.user && this.onUserJoined) {
            this.onUserJoined(message.user);
          }
          break;

        case MessageType.USER_LEFT:
          // Notify that a user left
          if (message.user_id && message.username && this.onUserLeft) {
            this.onUserLeft(message.user_id, message.username);
          }
          break;

        case MessageType.PING:
          // Respond to heartbeat
          this.sendMessage({ type: MessageType.PONG });
          break;

        case MessageType.ERROR:
          // Handle error message
          console.error('Server error:', message.message);
          if (this.onError) {
            this.onError(message.message || 'Unknown error');
          }
          break;

        case MessageType.SERVER_SHUTDOWN:
          // Server is shutting down, prepare to reconnect
          console.log('Server shutting down, will reconnect');
          if (message.reconnect) {
            this.scheduleReconnect();
          }
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error handling message:', error);
    }
  }

  /**
   * Send a message to the WebSocket server
   */
  private sendMessage(message: WebSocketMessage) {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      // Queue message for later sending
      this.messageQueue.push(message);
      return;
    }

    try {
      this.websocket.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending message:', error);
      this.messageQueue.push(message);
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect() {
    if (this.reconnectTimeout) {
      return; // Already scheduled
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.websocket) {
      this.websocket.close(1000, 'Normal closure');
      this.websocket = null;
    }

    this.isConnected = false;
  }

  /**
   * Update local user awareness (cursor position, etc.)
   */
  public updateAwareness(awareness: Partial<UserAwareness>) {
    if (this.awareness) {
      const currentState = this.awareness.getLocalState() || {};
      this.awareness.setLocalState({
        ...currentState,
        ...awareness,
      });
    }
  }

  /**
   * Get the Yjs document
   */
  public getYDoc(): Y.Doc {
    return this.yDoc;
  }

  /**
   * Get the Yjs text type
   */
  public getYText(): Y.Text {
    return this.yText;
  }

  /**
   * Get the awareness instance
   */
  public getAwareness(): Awareness | null {
    return this.awareness;
  }

  /**
   * Check if connected
   */
  public get connected(): boolean {
    return this.isConnected;
  }

  /**
   * Convert ArrayBuffer to Base64
   */
  private arrayBufferToBase64(buffer: Uint8Array): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 to ArrayBuffer
   */
  private base64ToArrayBuffer(base64: string): Uint8Array {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
  }

  /**
   * Cleanup resources
   */
  public destroy() {
    this.disconnect();
    this.yDoc.destroy();
  }
}

/**
 * Create a collaboration manager for a document
 */
export function createCollaborationManager(
  documentId: string,
  token: string,
  wsUrl?: string
): CollaborationManager {
  return new CollaborationManager(documentId, token, wsUrl);
}
