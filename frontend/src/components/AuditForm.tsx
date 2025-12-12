import { useState, useEffect } from 'react';
import type { ExtractedData, ValidationIssue } from '../types/contract';
import FieldWithError from './FieldWithError';

interface AuditFormProps {
  data: ExtractedData;
  validationIssues: ValidationIssue[];
  onSave: (data: ExtractedData) => void;
  onApprove: (data: ExtractedData) => void;
  disabled?: boolean;
}

export default function AuditForm({
  data,
  validationIssues,
  onSave,
  onApprove,
  disabled = false,
}: AuditFormProps) {
  const [formData, setFormData] = useState<ExtractedData>(data);

  // Update form data when the contract data changes (e.g., navigating to different contract)
  useEffect(() => {
    setFormData(data);
  }, [data]);

  const getFieldError = (fieldName: string): ValidationIssue | undefined => {
    return validationIssues.find((issue) => issue.field === fieldName);
  };

  const handleChange = (field: keyof ExtractedData, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePartyChange = (index: number, field: 'name' | 'role', value: string) => {
    const newParties = [...formData.parties];
    newParties[index] = { ...newParties[index], [field]: value };
    setFormData((prev) => ({
      ...prev,
      parties: newParties,
    }));
  };

  return (
    <div className="space-y-6">
      {/* Parties Section */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Contract Parties
        </h3>
        {formData.parties.map((party, index) => (
          <div key={index} className="flex gap-4 mb-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">
                Party {index + 1} Name
              </label>
              <input
                type="text"
                value={party.name}
                onChange={(e) => handlePartyChange(index, 'name', e.target.value)}
                disabled={disabled}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
            <div className="w-1/3">
              <label className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <input
                type="text"
                value={party.role || ''}
                onChange={(e) => handlePartyChange(index, 'role', e.target.value)}
                disabled={disabled}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
          </div>
        ))}
      </section>

      {/* Dates and Duration */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Dates & Duration
        </h3>
        <FieldWithError
          label="Effective Date"
          name="effective_date"
          type="date"
          value={formData.effective_date || ''}
          onChange={(value) => handleChange('effective_date', value)}
          error={getFieldError('effective_date')}
          disabled={disabled}
        />
        <FieldWithError
          label="Duration (months)"
          name="contract_duration_months"
          type="number"
          value={formData.contract_duration_months ?? ''}
          onChange={(value) =>
            handleChange('contract_duration_months', parseInt(value) || 0)
          }
          error={getFieldError('contract_duration_months')}
          disabled={disabled}
        />
        {formData.contract_duration_raw && (
          <p className="text-sm text-gray-500 -mt-2 mb-4">
            Original text: "{formData.contract_duration_raw}"
          </p>
        )}
      </section>

      {/* Jurisdiction */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Jurisdiction</h3>
        <FieldWithError
          label="Governing Law"
          name="jurisdiction"
          value={formData.jurisdiction || ''}
          onChange={(value) => handleChange('jurisdiction', value)}
          error={getFieldError('jurisdiction')}
          disabled={disabled}
        />
      </section>

      {/* Risk Score */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Risk Assessment
        </h3>
        <FieldWithError
          label="Risk Score (1-100)"
          name="risk_score"
          type="number"
          value={formData.risk_score}
          onChange={(value) => {
            const num = Math.min(100, Math.max(1, parseInt(value) || 1));
            handleChange('risk_score', num);
          }}
          error={getFieldError('risk_score')}
          disabled={disabled}
        />
        <div className="mt-2">
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  formData.risk_score > 70
                    ? 'bg-red-500'
                    : formData.risk_score > 40
                    ? 'bg-amber-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${formData.risk_score}%` }}
              />
            </div>
            <span
              className={`text-sm font-medium ${
                formData.risk_score > 70
                  ? 'text-red-600'
                  : formData.risk_score > 40
                  ? 'text-amber-600'
                  : 'text-green-600'
              }`}
            >
              {formData.risk_score > 70
                ? 'High Risk'
                : formData.risk_score > 40
                ? 'Medium Risk'
                : 'Low Risk'}
            </span>
          </div>
        </div>
      </section>

      {/* Actions */}
      {!disabled && (
        <div className="flex gap-4 pt-4 border-t">
          <button
            type="button"
            onClick={() => onSave(formData)}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Save Changes
          </button>
          <button
            type="button"
            onClick={() => onApprove(formData)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            Approve Contract
          </button>
        </div>
      )}
    </div>
  );
}
