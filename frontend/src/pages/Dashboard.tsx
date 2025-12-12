import { useState, useEffect, useCallback } from 'react';
import { contractsApi } from '../services/api';
import ContractList from '../components/ContractList';
import type { Contract } from '../types/contract';

export default function Dashboard() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');

  const fetchContracts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await contractsApi.list();
      setContracts(response.contracts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contracts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContracts();
  }, [fetchContracts]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF file');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress('Uploading and analyzing contract...');
      setError(null);

      const result = await contractsApi.audit(file);

      setUploadProgress(
        `Analysis complete! Processing took ${result.processing_time_ms}ms`
      );

      // Refresh the list
      await fetchContracts();

      // Clear progress after a moment
      setTimeout(() => setUploadProgress(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload contract');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  // Categorize contracts
  const needsReview = contracts.filter((c) => c.requires_human_review);
  const approved = contracts.filter((c) => c.status === 'approved');
  const processing = contracts.filter((c) => c.status === 'processing');
  const rejected = contracts.filter((c) => c.status === 'rejected');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading contracts...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-amber-700">{needsReview.length}</div>
          <div className="text-sm text-amber-600">Needs Review</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-700">{approved.length}</div>
          <div className="text-sm text-green-600">Approved</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-700">{processing.length}</div>
          <div className="text-sm text-blue-600">Processing</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-700">{rejected.length}</div>
          <div className="text-sm text-red-600">Rejected</div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="mb-8 p-6 bg-white rounded-lg shadow border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Upload New Contract
        </h2>
        <div className="flex items-center gap-4">
          <label
            className={`flex-1 border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              uploading
                ? 'border-gray-300 bg-gray-50'
                : 'border-blue-300 hover:border-blue-500 hover:bg-blue-50'
            }`}
          >
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
            {uploading ? (
              <div className="text-gray-500">
                <svg
                  className="animate-spin h-8 w-8 mx-auto mb-2 text-blue-500"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {uploadProgress}
              </div>
            ) : (
              <div>
                <svg
                  className="h-12 w-12 mx-auto mb-2 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-blue-600 font-medium">
                  Click to upload PDF contract
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  The AI will analyze and extract key information
                </p>
              </div>
            )}
          </label>
        </div>

        {uploadProgress && !uploading && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm">
            {uploadProgress}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Contract Lists */}
      {needsReview.length > 0 && (
        <ContractList
          contracts={needsReview}
          title="Requires Human Review"
          emptyMessage="No contracts need review"
        />
      )}

      <ContractList
        contracts={approved}
        title="Approved Contracts"
        emptyMessage="No approved contracts yet"
      />

      {rejected.length > 0 && (
        <ContractList
          contracts={rejected}
          title="Rejected Contracts"
          emptyMessage="No rejected contracts"
        />
      )}
    </div>
  );
}
