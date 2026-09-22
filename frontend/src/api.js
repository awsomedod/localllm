async function request(path, signal, options = {}) {
  const response = await fetch(`/api${path}`, { signal, ...options })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (body?.detail) detail = body.detail
    } catch {
      // keep status text
    }
    throw new Error(detail)
  }
  return response.json()
}

function listQuery({ congress, offset = 0, limit = 20 }) {
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  })
  if (congress) params.set('congress', String(congress))
  return params
}

export function listMembers(options, signal) {
  return request(`/members?${listQuery(options)}`, signal)
}

export function getMember(bioguideId, congress, signal) {
  return request(`/members/${bioguideId}/${congress}`, signal)
}

export function listHouseVotes(options, signal) {
  return request(`/house-votes?${listQuery(options)}`, signal)
}

export function getHouseVote(identifier, signal) {
  return request(`/house-votes/${identifier}`, signal)
}

export async function streamHouseVoteSummary(identifier, handlers = {}, signal) {
  const response = await fetch(`/api/house-votes/${identifier}/summary`, {
    method: 'POST',
    signal,
  })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (body?.detail) detail = body.detail
    } catch {
      // keep status text
    }
    throw new Error(detail)
  }
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('event-stream')) {
    const vote = await response.json()
    handlers.onDone?.(vote.summary || '', vote)
    return
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    const frames = buffer.split('\n\n')
    buffer = frames.pop() || ''
    for (const frame of frames) {
      const line = frame.split('\n').find((part) => part.startsWith('data:'))
      if (!line) continue
      const event = JSON.parse(line.slice(5).trim())
      if (event.type === 'status') handlers.onStatus?.(event.message)
      else if (event.type === 'reset') handlers.onReset?.()
      else if (event.type === 'delta') handlers.onDelta?.(event.text)
      else if (event.type === 'done') handlers.onDone?.(event.summary)
      else if (event.type === 'error') throw new Error(event.detail || 'Summarizer failed')
    }
  }
}
