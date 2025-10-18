import apiClient from './api';
import { Document, DocumentCreate, DocumentUpdate, DocumentList } from '@/types/document';

export const documentService = {
  // Get all documents for the current user
  async getDocuments(skip: number = 0, limit: number = 100): Promise<DocumentList> {
    const response = await apiClient.get<DocumentList>('/documents', {
      params: { skip, limit }
    });
    return response.data;
  },

  // Get a specific document by ID
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/documents/${documentId}`);
    return response.data;
  },

  // Create a new document
  async createDocument(document: DocumentCreate): Promise<Document> {
    const response = await apiClient.post<Document>('/documents/', document);
    return response.data;
  },

  // Update an existing document
  async updateDocument(documentId: string, update: DocumentUpdate): Promise<Document> {
    const response = await apiClient.put<Document>(`/documents/${documentId}`, update);
    return response.data;
  },

  // Delete a document
  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`);
  }
};
