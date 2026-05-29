import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { getBatches, getBatch } from '../api/ingestion'
import { approveRow, rejectRow, flagRow, bulkApprove } from '../api/review'

const TENANT_ID = 1

function StatusBadge({ status }) {
  return <span className={`badge ${status}`}>{status}</span>
}

export default function Review() {
  const { batchId } = useParams()
  const navigate = useNavigate()

  const [batches, setBatches] = useState([])
  const [selected, setSelected] = useState(null)
  const [emissions, setEmissions] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getBatches(TENANT_ID).then((r) => setBatches(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!batchId) return
    setLoading(true)
    getBatch(TENANT_ID, batchId)
      .then((r) => {
        setSelected(r.data.batch)
        setEmissions(r.data.emissions)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [batchId])

  const refresh = () => {
    if (!batchId) return
    getBatch(TENANT_ID, batchId).then((r) => {
      setSelected(r.data.batch)
      setEmissions(r.data.emissions)
    })
  }

  const act = async (fn, ...args) => {
    try { await fn(...args); refresh() }
    catch (e) { setError(e.message) }
  }

  const handleBulkApprove = async () => {
    try { await bulkApprove(batchId); refresh() }
    catch (e) { setError(e.message) }
  }

  const filtered = statusFilter === 'all'
    ? emissions
    : emissions.filter((e) => e.status === statusFilter)

  const counts = emissions.reduce((acc, e) => {
    acc[e.status] = (acc[e.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="layout">
      <Nav />
      <main className="main">
        <div className="page-title">Review</div>

        {error && <div className="alert alert-error">{error}</div>}

        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
          {/* Batch list */}
          <div style={{ width: 220, flexShrink: 0 }}>
            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #eee', fontWeight: 600, fontSize: 13 }}>
                Batches
              </div>
              {batches.length === 0 && <div className="empty" style={{ padding: 20 }}>No batches</div>}
              {batches.map((b) => (
                <div
                  key={b.id}
                  onClick={() => navigate(`/review/${b.id}`)}
                  style={{
                    padding: '10px 16px', cursor: 'pointer', borderBottom: '1px solid #f5f5f5',
                    background: String(b.id) === String(batchId) ? '#f0f5ff' : 'transparent',
                    borderLeft: String(b.id) === String(batchId) ? '3px solid #4f8ef7' : '3px solid transparent',
                  }}
                >
                  <div style={{ fontSize: 12, fontWeight: 600 }}>
                    <span className={`badge ${b.source}`}>{b.source}</span> #{b.id}
                  </div>
                  <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
                    {new Date(b.uploaded_at).toLocaleDateString()}
                    &nbsp;·&nbsp;{b.total_rows} rows
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Emission rows */}
          <div style={{ flex: 1 }}>
            {!batchId && <div className="empty">Select a batch to review its rows.</div>}
            {batchId && loading && <div className="empty">Loading...</div>}
            {batchId && !loading && selected && (
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div>
                    <strong>Batch #{selected.id}</strong>
                    &nbsp;·&nbsp;<span className={`badge ${selected.source}`}>{selected.source}</span>
                    &nbsp;·&nbsp;{selected.total_rows} rows
                    &nbsp;·&nbsp;<span style={{ color: '#10b981' }}>{selected.parsed_rows} parsed</span>
                    {selected.failed_rows > 0 && <span style={{ color: '#ef4444' }}>&nbsp;·&nbsp;{selected.failed_rows} failed</span>}
                  </div>
                  <button className="btn btn-success btn-sm" onClick={handleBulkApprove}>
                    Bulk approve pending
                  </button>
                </div>

                <div style={{ display: 'flex', gap: 8, marginBottom: 12, fontSize: 12 }}>
                  {['all', 'pending', 'approved', 'rejected', 'flagged'].map((s) => (
                    <button
                      key={s}
                      className={`btn btn-sm ${statusFilter === s ? 'btn-primary' : 'btn-ghost'}`}
                      onClick={() => setStatusFilter(s)}
                    >
                      {s} {s === 'all' ? `(${emissions.length})` : counts[s] ? `(${counts[s]})` : ''}
                    </button>
                  ))}
                </div>

                {filtered.length === 0 ? (
                  <div className="empty">No rows for this filter.</div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Date</th>
                          <th>Scope</th>
                          <th>Description</th>
                          <th>kgCO2e</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((em) => (
                          <tr key={em.id}>
                            <td style={{ color: '#888' }}>#{em.id}</td>
                            <td>{em.activity_date}</td>
                            <td>{em.scope}</td>
                            <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {em.description || '—'}
                            </td>
                            <td>{Number(em.co2e_kg).toLocaleString('en-US', { maximumFractionDigits: 1 })}</td>
                            <td><StatusBadge status={em.status} /></td>
                            <td>
                              {em.status !== 'approved' && (
                                <div className="row-actions">
                                  <button className="btn btn-success btn-sm" onClick={() => act(approveRow, em.id)}>✓</button>
                                  <button className="btn btn-danger btn-sm" onClick={() => act(rejectRow, em.id)}>✗</button>
                                  <button className="btn btn-warning btn-sm" onClick={() => act(flagRow, em.id, 'manual flag')}>⚑</button>
                                </div>
                              )}
                              {em.status === 'approved' && <span style={{ color: '#888', fontSize: 11 }}>locked</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
