import { Globe, ChevronDown } from 'lucide-react';
import { Country } from '../types';

const countries: Country[] = [
  {
    code: 'IN',
    name: 'India',
    standards: ['Indian GAAP', 'Ind AS', 'Companies Act 2013']
  },
  {
    code: 'US',
    name: 'United States',
    standards: ['US GAAP', 'SEC Regulations']
  },
  {
    code: 'GB',
    name: 'United Kingdom',
    standards: ['UK GAAP', 'IFRS']
  },
  {
    code: 'AE',
    name: 'United Arab Emirates',
    standards: ['IFRS', 'UAE Commercial Companies Law']
  },
  {
    code: 'CA',
    name: 'Canada',
    standards: ['IFRS', 'ASPE (Accounting Standards for Private Enterprises)', 'Canadian GAAP']
  },
  {
    code: 'SG',
    name: 'Singapore',
    standards: ['Singapore Financial Reporting Standards (SFRS)', 'IFRS']
  }
];

interface CountrySelectorProps {
  selectedCountry: string;
  onCountrySelect: (countryCode: string) => void;
}

export default function CountrySelector({ selectedCountry, onCountrySelect }: CountrySelectorProps) {
  const selectedCountryData = countries.find(country => country.code === selectedCountry);

  return (
    <div className="bg-white rounded-lg p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Globe className="h-5 w-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900">Select Country</h2>
      </div>
      
      <div className="relative">
        <select
          value={selectedCountry}
          onChange={(e) => onCountrySelect(e.target.value)}
          className="w-full p-3 bg-white border border-gray-300 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {countries.map((country) => (
            <option key={country.code} value={country.code}>
              {country.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
      </div>
      
      {selectedCountryData && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900">{selectedCountryData.name}</h3>
          <p className="text-sm text-gray-600 mt-1">
            Applicable Standards:
          </p>
          <ul className="mt-2 list-disc list-inside text-sm text-gray-600">
            {selectedCountryData.standards.map((standard, index) => (
              <li key={index}>{standard}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}