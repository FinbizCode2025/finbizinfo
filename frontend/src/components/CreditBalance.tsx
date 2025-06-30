import React from 'react';
import { CreditCard } from 'lucide-react';

export default function CreditBalance() {


  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-full shadow-sm border border-gray-200">
      <CreditCard className="h-4 w-4 text-blue-600" />
      <span className="text-sm font-medium">
      </span>
    </div>
  );
}