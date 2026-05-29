const API_BASE = import.meta.env.VITE_API_URL ?? ''

function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

async function request(path, options = {}) {
  const isWrite = options.method && options.method !== 'GET'
  const res = await fetch(API_BASE + path, {
    headers: {
      'Content-Type': 'application/json',
      ...(isWrite ? { 'X-CSRFToken': getCsrfToken() } : {}),
      ...options.headers,
    },
    credentials: 'include',
    ...options,
  })

  const text = await res.text()
  let json
  try {
    json = JSON.parse(text)
  } catch {
    throw new Error(`Server error ${res.status}`)
  }

  if (!res.ok) throw new Error(json.error || `Request failed (${res.status})`)
  return json
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  postForm: (path, formData) =>
    request(path, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrfToken() },
      body: formData,
    }),
}
