import { FileSpreadsheet, Settings, LogOut } from 'lucide-react';

export default function Header() {

  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileSpreadsheet className="h-8 w-8" />
            <h1 className="text-2xl font-semibold">
              Financial Analysis Suite
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-lg hover:bg-blue-500 transition-colors">
              <Settings className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}