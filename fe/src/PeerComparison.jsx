import React, { useState } from "react";

export default function PeerComparison() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [mainCIN, setMainCIN] = useState("");
  const [peer1CIN, setPeer1CIN] = useState("");
  const [peer2CIN, setPeer2CIN] = useState("");

  const handleCompare = async () => {
    if (!mainCIN) {
      alert("Please enter Main Company CIN");
      return;
    }

    setLoading(true);
    setResult(null);

    const cins = [mainCIN, peer1CIN, peer2CIN].filter(Boolean);

    try {
      const profiles = {};
      for (const cin of cins) {
        const res = await fetch(`http://127.0.0.1:5002/api/company/profile/${cin}`);
        if (!res.ok) throw new Error(`Failed to fetch data for CIN: ${cin}`);
        profiles[cin] = await res.json();
      }
      setResult(profiles);
    } catch (err) {
      console.error(err);
      alert(err.message || "Error fetching company profiles");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <div style={{ marginBottom: "12px" }}>
        <input
          type="text"
          placeholder="Main Company CIN"
          value={mainCIN}
          onChange={(e) => setMainCIN(e.target.value)}
          style={{ marginRight: "8px", padding: "4px" }}
        />
        <input
          type="text"
          placeholder="Peer 1 CIN"
          value={peer1CIN}
          onChange={(e) => setPeer1CIN(e.target.value)}
          style={{ marginRight: "8px", padding: "4px" }}
        />
        <input
          type="text"
          placeholder="Peer 2 CIN"
          value={peer2CIN}
          onChange={(e) => setPeer2CIN(e.target.value)}
          style={{ marginRight: "8px", padding: "4px" }}
        />
        <button onClick={handleCompare} disabled={loading} style={{ padding: "8px 12px" }}>
          {loading ? "Comparing..." : "Generate Peer Comparison"}
        </button>
      </div>

      {/* ---------------- Tables ---------------- */}
      {result &&
        Object.entries(result).map(([cin, profile]) => (
          <div key={cin} style={{ marginTop: "24px", border: "1px solid #ccc", padding: "12px", borderRadius: "8px" }}>
            <h3 style={{ marginBottom: "8px" }}>
              {profile.company?.name || "Unknown Company"} ({cin})
            </h3>

            {/* Company Info */}
            <table border={1} style={{ width: "100%", marginBottom: "12px", borderCollapse: "collapse" }}>
              <tbody>
                <tr>
                  <td style={{ fontWeight: "bold", padding: "4px" }}>Industry</td>
                  <td style={{ padding: "4px" }}>{profile.company?.industry || "-"}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: "bold", padding: "4px" }}>Sector</td>
                  <td style={{ padding: "4px" }}>{profile.company?.sector || "-"}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: "bold", padding: "4px" }}>Incorporation Year</td>
                  <td style={{ padding: "4px" }}>{profile.company?.incorporationYear || "-"}</td>
                </tr>
              </tbody>
            </table>

            {/* Financials */}
            {profile.financials?.length > 0 && (
              <table border={1} style={{ width: "100%", marginBottom: "12px", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Revenue</th>
                    <th>Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.financials.map((fin, idx) => (
                    <tr key={idx}>
                      <td>{fin.year || "-"}</td>
                      <td>{fin.revenue ?? "-"}</td>
                      <td>{fin.profit ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* Directors */}
            {profile.directors?.length > 0 && (
              <table border={1} style={{ width: "100%", marginBottom: "12px", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Designation</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.directors.map((dir, idx) => (
                    <tr key={idx}>
                      <td>{dir.name || "-"}</td>
                      <td>{dir.designation || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* Charges */}
            {profile.charges?.length > 0 && (
              <table border={1} style={{ width: "100%", marginBottom: "12px", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th>Charge ID</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.charges.map((ch, idx) => (
                    <tr key={idx}>
                      <td>{ch.charge_id || "-"}</td>
                      <td>{ch.amount ?? "-"}</td>
                      <td>{ch.status || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* Risk Flags */}
            {profile.riskFlags?.length > 0 && (
              <div>
                <strong>Risk Flags:</strong>
                <ul>
                  {profile.riskFlags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
    </div>
  );
}
