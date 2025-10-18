export interface CollaboratorInfo {
  user_id: string;
  username: string;
  email: string;
  access_type: 'owner' | 'editor';
  granted_at: string;
}

export interface ShareDocumentRequest {
  user_ids: string[];
}

export interface ShareResponse {
  document_id: string;
  shared_with: CollaboratorInfo[];
}

export interface CollaboratorsResponse {
  document_id: string;
  collaborators: CollaboratorInfo[];
}

export interface UserSearchResult {
  id: string;
  username: string;
  email: string;
}
