import { useState, useEffect } from 'react'
import Nav from '../components/Nav'
import { getGlobalAuditLog } from '../api/review'

const ACTION_LABELS = {
  approve: { label: 'Approved', color: '#16a34a' },
  reject:  { label: 'Rejected', color: '#dc2626' },
  flag:    { label: 'Flagged',  color: '#d97706' },
}

function formatDate(iso) {
  return new Date(iso).toLocaleString()
}

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getGlobalAuditLog()
      .then((res) => setLogs(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="layout">
      <Nav />
      <main className="main-content">
        <h1 className="page-title">Audit Log</h1>
        <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
          All approve / reject / flag actions across every batch, newest first.
        </p>

        {loading && <p>Loading…</p>}
        {error && <p style={{ color: '#dc2626' }}>{error}</p>}

        {!loading && !error && logs.length === 0 && (
          <p style={{ color: '#6b7280' }}>No actions recorded yet. Approve or reject a row to see entries here.</p>
        )}

        {!loading && logs.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Emission ID</th>
                  <th>Previous status</th>
                  <th>New status</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const action = ACTION_LABELS[log.action] || { label: log.action, color: '#6b7280' }
                  return (
                    <tr key={log.id}>
                      <td style={{ whiteSpace: 'nowrap' }}>{formatDate(log.performed_at)}</td>
                      <td>{log.performed_by}</td>
                      <td>
                        <span style={{
                          color: action.color,
                          fontWeight: 600,
                          textTransform: 'capitalize',
                        }}>
                          {action.label}
                        </span>
                      </td>
                      <td>#{log.emission}</td>
                      <td style={{ textTransform: 'capitalize', color: '#6b7280' }}>{log.previous_status}</td>
                      <td style={{ textTransform: 'capitalize', color: action.color }}>{log.new_status}</td>
                      <td style={{ color: '#6b7280' }}>{log.note || '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
