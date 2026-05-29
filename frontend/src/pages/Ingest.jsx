import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { uploadFile } from '../api/ingestion'

const TENANT_ID = 1
const SOURCES = ['sap', 'utility', 'travel']

export default function Ingest() {
  const [source, setSource] = useState('sap')
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const inputRef = useRef()
  const navigate = useNavigate()

  const detectSource = (filename) => {
    const name = filename.toLowerCase()
    if (name.includes('sap')) return 'sap'
    if (name.includes('utility') || name.includes('bill')) return 'utility'
    if (name.includes('travel')) return 'travel'
    return null
  }

  const pickFile = (f) => {
    if (!f) return
    setFile(f)
    const detected = detectSource(f.name)
    if (detected) setSource(detected)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) { setError('Please select a file'); return }
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const res = await uploadFile(TENANT_ID, source, file)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <Nav />
      <main className="main">
        <div className="page-title">Ingest Data</div>

        <div className="card" style={{ maxWidth: 560 }}>
          <div className="card-title">Upload a file</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Data source</label>
              <select value={source} onChange={(e) => setSource(e.target.value)}>
                {SOURCES.map((s) => (
                  <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>File (CSV)</label>
              <div
                className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current.click()}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept=".csv"
                  onChange={(e) => pickFile(e.target.files[0])}
                />
                {file
                  ? <span style={{ color: '#1a1a1a', fontWeight: 500 }}>{file.name}</span>
                  : <span>Click to select or drag a CSV file here</span>
                }
              </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <button className="btn btn-primary" disabled={loading}>
              {loading ? 'Uploading...' : 'Upload and parse'}
            </button>
          </form>
        </div>

        {result && (
          <div className="card" style={{ maxWidth: 560 }}>
            <div className="card-title">Upload result</div>
            <div className="alert alert-success" style={{ marginBottom: 12 }}>
              Batch #{result.data.id} created successfully
            </div>
            <table>
              <tbody>
                <tr><td>Total rows</td><td><strong>{result.data.total_rows}</strong></td></tr>
                <tr><td>Parsed</td><td><strong style={{ color: '#10b981' }}>{result.data.parsed_rows}</strong></td></tr>
                <tr><td>Failed</td><td><strong style={{ color: result.data.failed_rows > 0 ? '#ef4444' : '#888' }}>{result.data.failed_rows}</strong></td></tr>
                <tr><td>Warnings</td><td><strong>{result.meta.warnings}</strong></td></tr>
              </tbody>
            </table>
            <div style={{ marginTop: 16 }}>
              <button className="btn btn-primary" onClick={() => navigate(`/review/${result.data.id}`)}>
                Review this batch
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
