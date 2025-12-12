import type { Contract } from '../types/contract';
import ContractCard from './ContractCard';

interface ContractListProps {
  contracts: Contract[];
  title: string;
  emptyMessage?: string;
}

export default function ContractList({
  contracts,
  title,
  emptyMessage = 'No contracts found',
}: ContractListProps) {
  if (contracts.length === 0) {
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
        <p className="text-gray-500 text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        {title} ({contracts.length})
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {contracts.map((contract) => (
          <ContractCard key={contract.id} contract={contract} />
        ))}
      </div>
    </div>
  );
}
