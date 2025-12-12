import { Link } from 'react-router-dom';
import type { Contract } from '../types/contract';

interface ContractCardProps {
  contract: Contract;
}

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: 'Pending', color: 'text-gray-700', bg: 'bg-gray-100' },
  processing: { label: 'Processing', color: 'text-blue-700', bg: 'bg-blue-100' },
  approved: { label: 'Approved', color: 'text-green-700', bg: 'bg-green-100' },
  requires_human_review: { label: 'Needs Review', color: 'text-amber-700', bg: 'bg-amber-100' },
  rejected: { label: 'Rejected', color: 'text-red-700', bg: 'bg-red-100' },
};

export default function ContractCard({ contract }: ContractCardProps) {
  const status = statusConfig[contract.status] || statusConfig.pending;

  return (
    <Link
      to={`/contracts/${contract.id}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200"
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {contract.file_name}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {new Date(contract.created_at).toLocaleDateString()}
            </p>
          </div>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.bg} ${status.color}`}
          >
            {status.label}
          </span>
        </div>

        {contract.extracted_data && (
          <div className="mt-3 space-y-1">
            {contract.extracted_data.jurisdiction && (
              <p className="text-xs text-gray-600">
                <span className="font-medium">Jurisdiction:</span>{' '}
                {contract.extracted_data.jurisdiction}
              </p>
            )}
            {contract.extracted_data.contract_duration_months && (
              <p className="text-xs text-gray-600">
                <span className="font-medium">Duration:</span>{' '}
                {contract.extracted_data.contract_duration_months} months
              </p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-gray-500">Risk:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    contract.extracted_data.risk_score > 70
                      ? 'bg-red-500'
                      : contract.extracted_data.risk_score > 40
                      ? 'bg-amber-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${contract.extracted_data.risk_score}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">
                {contract.extracted_data.risk_score}
              </span>
            </div>
          </div>
        )}

        {contract.validation_issues.length > 0 && (
          <div className="mt-3 flex items-center gap-1">
            <svg
              className="w-4 h-4 text-amber-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-xs text-amber-600">
              {contract.validation_issues.length} issue(s)
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}
