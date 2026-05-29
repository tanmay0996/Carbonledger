async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    credentials: 'include',
    ...options,
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.error || 'request failed')
  return json
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  postForm: (path, formData) =>
    request(path, {
      method: 'POST',
      headers: {},
      body: formData,
    }),
}
