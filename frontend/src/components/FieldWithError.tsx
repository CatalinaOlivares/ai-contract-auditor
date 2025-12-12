import type { ValidationIssue } from '../types/contract';

interface FieldWithErrorProps {
  label: string;
  name: string;
  value: string | number | null | undefined;
  type?: 'text' | 'number' | 'date';
  onChange: (value: string) => void;
  error?: ValidationIssue;
  disabled?: boolean;
  isModified?: boolean;
}

export default function FieldWithError({
  label,
  name,
  value,
  type = 'text',
  onChange,
  error,
  disabled = false,
  isModified = false,
}: FieldWithErrorProps) {
  const hasError = !!error;

  const getBorderClass = () => {
    if (hasError) return 'border-red-500 ring-red-500 focus:border-red-500 focus:ring-red-500';
    if (isModified) return 'border-blue-400 ring-blue-400 focus:border-blue-500 focus:ring-blue-500 bg-blue-50';
    return 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
  };

  return (
    <div className="mb-4">
      <label
        htmlFor={name}
        className={`block text-sm font-medium ${
          hasError ? 'text-red-600' : 'text-gray-700'
        }`}
      >
        {label}
        {isModified && !hasError && (
          <span className="ml-2 text-xs text-blue-600">(modified)</span>
        )}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${getBorderClass()} ${
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        }`}
      />

      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600 font-medium">{error.message}</p>
          {error.reasoning && (
            <p className="text-xs text-red-500 mt-1">
              Reasoning: {error.reasoning}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
