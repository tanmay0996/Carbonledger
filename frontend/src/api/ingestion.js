import { api } from './client'

export const getBatches = (tenantId) =>
  api.get(`/api/ingestion/batches/?tenant_id=${tenantId}`)

export const getBatch = (tenantId, batchId) =>
  api.get(`/api/ingestion/batches/${batchId}/?tenant_id=${tenantId}`)

export const uploadFile = (tenantId, source, file) => {
  const form = new FormData()
  form.append('tenant_id', tenantId)
  form.append('source', source)
  form.append('file', file)
  return api.postForm('/api/ingestion/upload/', form)
}
