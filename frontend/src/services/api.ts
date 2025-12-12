import axios from 'axios';
import type { Contract, ContractListResponse, AuditResponse, ExtractedData } from '../types/contract';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const contractsApi = {
  // List all contracts
  list: async (): Promise<ContractListResponse> => {
    const response = await api.get<ContractListResponse>('/contracts');
    return response.data;
  },

  // Get single contract
  get: async (id: string): Promise<Contract> => {
    const response = await api.get<Contract>(`/contracts/${id}`);
    return response.data;
  },

  // Upload and audit a contract
  audit: async (file: File): Promise<AuditResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<AuditResponse>('/audit', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Update contract (human correction)
  update: async (
    id: string,
    extractedData: ExtractedData,
    humanApproved: boolean = false,
    reviewerNotes?: string
  ): Promise<Contract> => {
    const response = await api.put<Contract>(`/contracts/${id}`, {
      extracted_data: extractedData,
      human_approved: humanApproved,
      reviewer_notes: reviewerNotes,
    });
    return response.data;
  },

  // Delete contract
  delete: async (id: string): Promise<void> => {
    await api.delete(`/contracts/${id}`);
  },

  // Get contract raw text
  getText: async (id: string): Promise<string> => {
    const response = await api.get<{ text: string }>(`/contracts/${id}/text`);
    return response.data.text;
  },
};

export default api;
