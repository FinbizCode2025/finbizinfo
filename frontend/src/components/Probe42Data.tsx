import React, { useEffect, useState } from "react";

interface Probe42DataProps {
  cins: string[]; // list of CINs
}

// Types for company profile response
interface CompanyProfile {
  company?: {
    name?: string;
    industry?: string;
    sector?: string;
    incorporationYear?: string;
  };
  financials?: { year?: string; revenue?: number; profit?: number }[];
  directors?: { name?: string; designation?: string }[];
  charges?: { charge_id?: string; amount?: number; status?: string }[];
  riskFlags?: string[];
  [key: string]: any;
}

export default function Probe42Data({ cins }: Probe42DataProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Record<string, CompanyProfile>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cins || cins.length === 0) return;

    const fetchProfiles = async () => {
      setLoading(true);
      setError(null);
      const results: Record<string, CompanyProfile> = {};

      try {
        for (const cin of cins) {
          const response = await fetch(`/api/company/profile/${cin}`);
          if (!response.ok) throw new Error(`Failed to fetch data for CIN: ${cin}`);
          const json = await response.json();
          results[cin] = json;
        }
        setData(results);
      } catch (err: any) {
        setError(err.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchProfiles();
  }, [cins]);

  if (loading) return <p>Loading company data...</p>;
  if (error) return <p className="text-red-500">Error: {error}</p>;
  if (!data || Object.keys(data).length === 0) return <p>No data available</p>;

  return (
    <div className="w-full overflow-x-auto space-y-6">
      {cins.map((cin) => {
        const profile = data[cin];
        if (!profile) return null;

        return (
          <div key={cin} className="border p-4 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-2">
              {profile.company?.name || "Unknown Company"} ({cin})
            </h3>

            {/* Company Info */}
            <div className="mb-4">
              <h4 className="font-medium">Basic Info</h4>
              <table className="min-w-full border border-gray-200">
                <tbody>
                  <tr>
                    <td className="border px-2 py-1 font-medium">Industry</td>
                    <td className="border px-2 py-1">{profile.company?.industry || "-"}</td>
                  </tr>
                  <tr>
                    <td className="border px-2 py-1 font-medium">Sector</td>
                    <td className="border px-2 py-1">{profile.company?.sector || "-"}</td>
                  </tr>
                  <tr>
                    <td className="border px-2 py-1 font-medium">Incorporation Year</td>
                    <td className="border px-2 py-1">{profile.company?.incorporationYear || "-"}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Financials */}
            {profile.financials?.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium">Financials</h4>
                <table className="min-w-full border border-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-2 py-1">Year</th>
                      <th className="border px-2 py-1">Revenue</th>
                      <th className="border px-2 py-1">Profit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.financials.map((fin, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="border px-2 py-1">{fin.year || "-"}</td>
                        <td className="border px-2 py-1">{fin.revenue ?? "-"}</td>
                        <td className="border px-2 py-1">{fin.profit ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Directors */}
            {profile.directors?.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium">Directors</h4>
                <table className="min-w-full border border-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-2 py-1">Name</th>
                      <th className="border px-2 py-1">Designation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.directors.map((dir, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="border px-2 py-1">{dir.name || "-"}</td>
                        <td className="border px-2 py-1">{dir.designation || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Charges */}
            {profile.charges?.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium">Charges</h4>
                <table className="min-w-full border border-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-2 py-1">Charge ID</th>
                      <th className="border px-2 py-1">Amount</th>
                      <th className="border px-2 py-1">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.charges.map((ch, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="border px-2 py-1">{ch.charge_id || "-"}</td>
                        <td className="border px-2 py-1">{ch.amount ?? "-"}</td>
                        <td className="border px-2 py-1">{ch.status || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Risk Flags */}
            {profile.riskFlags?.length > 0 && (
              <div>
                <h4 className="font-medium">Risk Flags</h4>
                <ul className="list-disc list-inside">
                  {profile.riskFlags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
