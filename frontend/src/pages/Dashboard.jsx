import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { getSummary } from '../api/emissions'
import { getBatches } from '../api/ingestion'

const TENANT_ID = 1

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [batches, setBatches] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getSummary(TENANT_ID)
      .then((r) => setSummary(r.data))
      .catch((e) => setError(e.message))

    getBatches(TENANT_ID)
      .then((r) => setBatches(r.data))
      .catch(() => {})
  }, [])

  const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 }))

  return (
    <div className="layout">
      <Nav />
      <main className="main">
        <div className="page-title">Dashboard</div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="summary-grid">
          <div className="tile scope1">
            <div className="label">Scope 1 — Direct</div>
            <div className="value">{fmt(summary?.scope_1)}</div>
            <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>kgCO2e approved</div>
          </div>
          <div className="tile scope2">
            <div className="label">Scope 2 — Electricity</div>
            <div className="value">{fmt(summary?.scope_2)}</div>
            <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>kgCO2e approved</div>
          </div>
          <div className="tile scope3">
            <div className="label">Scope 3 — Travel</div>
            <div className="value">{fmt(summary?.scope_3)}</div>
            <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>kgCO2e approved</div>
          </div>
          <div className="tile total">
            <div className="label">Total Emissions</div>
            <div className="value">{fmt(summary?.total)}</div>
            <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>kgCO2e approved</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Recent Ingestion Batches</div>
          {batches.length === 0 ? (
            <div className="empty">No batches yet. Go to Ingest to upload data.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Source</th>
                    <th>Uploaded</th>
                    <th>Total</th>
                    <th>Parsed</th>
                    <th>Failed</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {batches.slice(0, 10).map((b) => (
                    <tr key={b.id}>
                      <td>#{b.id}</td>
                      <td><span className={`badge ${b.source}`}>{b.source}</span></td>
                      <td>{new Date(b.uploaded_at).toLocaleString()}</td>
                      <td>{b.total_rows}</td>
                      <td style={{ color: '#10b981' }}>{b.parsed_rows}</td>
                      <td style={{ color: b.failed_rows > 0 ? '#ef4444' : '#888' }}>{b.failed_rows}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/review/${b.id}`)}>
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
