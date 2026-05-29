import { api } from './client'

export const getEmissions = (tenantId, params = {}) => {
  const qs = new URLSearchParams({ tenant_id: tenantId, ...params }).toString()
  return api.get(`/api/emissions/?${qs}`)
}

export const getSummary = (tenantId) =>
  api.get(`/api/emissions/summary/?tenant_id=${tenantId}`)
