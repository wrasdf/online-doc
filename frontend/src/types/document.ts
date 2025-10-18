export interface Document {
  id: string;
  title: string;
  content: string;
  owner_id: string;
  version: number;
  created_at: string;
  updated_at: string;
  yjs_state?: Uint8Array | null;
}

export interface DocumentCreate {
  title: string;
  content?: string;
}

export interface DocumentUpdate {
  title?: string;
  content?: string;
  yjs_state?: Uint8Array;
}

export interface DocumentList {
  documents: Document[];
  total: number;
}
