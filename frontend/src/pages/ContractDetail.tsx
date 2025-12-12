import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { contractsApi } from '../services/api';
import PDFViewer from '../components/PDFViewer';
import AuditForm from '../components/AuditForm';
import type { Contract, ExtractedData } from '../types/contract';

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: 'Pending', color: 'text-gray-700', bg: 'bg-gray-100' },
  processing: { label: 'Processing', color: 'text-blue-700', bg: 'bg-blue-100' },
  approved: { label: 'Approved', color: 'text-green-700', bg: 'bg-green-100' },
  requires_human_review: { label: 'Needs Review', color: 'text-amber-700', bg: 'bg-amber-100' },
  rejected: { label: 'Rejected', color: 'text-red-700', bg: 'bg-red-100' },
};

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>();
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchContract = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const data = await contractsApi.get(id);
        setContract(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contract');
      } finally {
        setLoading(false);
      }
    };

    fetchContract();
  }, [id]);

  const handleSave = async (data: ExtractedData) => {
    if (!id) return;

    try {
      setSaving(true);
      setMessage(null);
      const updated = await contractsApi.update(id, data, false);
      setContract(updated);
      setMessage('Changes saved successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async (data: ExtractedData) => {
    if (!id) return;

    try {
      setSaving(true);
      setMessage(null);
      const updated = await contractsApi.update(id, data, true);
      setContract(updated);
      setMessage('Contract approved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve contract');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading contract...</div>
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-red-700">{error || 'Contract not found'}</p>
        <Link to="/" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const status = statusConfig[contract.status] || statusConfig.pending;

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:underline text-sm">
          &larr; Back to Dashboard
        </Link>
        <div className="flex items-center justify-between mt-2">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{contract.file_name}</h1>
            <p className="text-sm text-gray-500">
              Uploaded {new Date(contract.created_at).toLocaleString()}
            </p>
          </div>
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${status.bg} ${status.color}`}
          >
            {status.label}
          </span>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-700">
          {message}
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
          {error}
        </div>
      )}

      {/* Validation Issues Banner */}
      {contract.validation_issues.length > 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="text-amber-800 font-medium mb-2">
            Validation Issues ({contract.validation_issues.length})
          </h3>
          <ul className="space-y-2">
            {contract.validation_issues.map((issue, index) => (
              <li key={index} className="text-sm text-amber-700">
                <span className="font-medium">{issue.field}:</span> {issue.message}
              </li>
            ))}
          </ul>
          {contract.review_reasons.length > 0 && (
            <div className="mt-3 pt-3 border-t border-amber-200">
              <p className="text-sm text-amber-800 font-medium">Review Reasons:</p>
              <ul className="mt-1 list-disc list-inside text-sm text-amber-700">
                {contract.review_reasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side View */}
      <div className="grid grid-cols-2 gap-6 h-[calc(100vh-300px)] min-h-[500px]">
        {/* Left: PDF/Text Viewer */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
            <h2 className="text-sm font-medium text-gray-700">Contract Text</h2>
          </div>
          <div className="h-[calc(100%-40px)]">
            <PDFViewer contractId={contract.id} />
          </div>
        </div>

        {/* Right: Audit Form */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-700">Extracted Data</h2>
            {contract.confidence_score !== null && (
              <span className="text-xs text-gray-500">
                Confidence: {Math.round((contract.confidence_score || 0) * 100)}%
              </span>
            )}
          </div>
          <div className="h-[calc(100%-40px)] overflow-y-auto p-4">
            {contract.extracted_data ? (
              <AuditForm
                data={contract.extracted_data}
                validationIssues={contract.validation_issues}
                onSave={handleSave}
                onApprove={handleApprove}
                disabled={saving || contract.human_approved}
              />
            ) : (
              <p className="text-gray-500">No data extracted yet</p>
            )}

            {contract.human_approved && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-green-700 text-sm font-medium">
                  This contract has been approved by a human reviewer.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
