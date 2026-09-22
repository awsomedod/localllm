import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getHouseVote, streamHouseVoteSummary } from '../api'
import Status from '../components/Status'
import { formatDate, legislationLabel } from '../format'

export default function VoteDetailPage() {
  const { identifier } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [vote, setVote] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [summarizing, setSummarizing] = useState(false)
  const [summaryError, setSummaryError] = useState('')
  const [draft, setDraft] = useState('')
  const [streamStatus, setStreamStatus] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    setModalOpen(false)
    setSummarizing(false)
    setSummaryError('')
    setDraft('')
    setStreamStatus('')
    getHouseVote(identifier, controller.signal)
      .then((payload) => {
        setVote(payload)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(err.message)
        setLoading(false)
      })
    return () => controller.abort()
  }, [identifier])

  useEffect(() => {
    if (!modalOpen) return undefined
    const onKey = (event) => {
      if (event.key === 'Escape' && !summarizing) setModalOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [modalOpen, summarizing])

  const tallies = useMemo(() => {
    const counts = {}
    for (const position of vote?.positions || []) {
      const key = position.vote_cast || 'Unknown'
      counts[key] = (counts[key] || 0) + 1
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [vote])

  const text = vote?.text && typeof vote.text === 'object' ? vote.text : null

  function openExistingSummary() {
    setSummaryError('')
    setModalOpen(true)
  }

  function startSummarize() {
    setSummaryError('')
    setDraft('')
    setStreamStatus('Starting…')
    setModalOpen(true)
    setSummarizing(true)
    streamHouseVoteSummary(identifier, {
      onStatus: (message) => setStreamStatus(message),
      onReset: () => setDraft(''),
      onDelta: (text) => setDraft((current) => current + text),
      onDone: (summary) => {
        setVote((current) => (current ? { ...current, summary } : current))
        setDraft('')
        setStreamStatus('')
        setSummarizing(false)
      },
    }).catch((err) => {
      if (err.name === 'AbortError') return
      setSummaryError(err.message)
      setSummarizing(false)
    })
  }

  return (
    <section>
      <p className="crumb">
        <Link to="/votes">House votes</Link>
      </p>
      <Status loading={loading} error={error}>
        {vote && (
          <>
            <div className="page-head">
              <div>
                <h1>
                  Session {vote.sessionNumber}, roll {vote.rollCallNumber}
                </h1>
                <p className="muted">
                  {formatDate(vote.startDate)} · {vote.voteType} · {vote.result}
                </p>
              </div>
            </div>
            <dl className="facts">
              <div>
                <dt>Identifier</dt>
                <dd>{vote.identifier}</dd>
              </div>
              <div>
                <dt>Legislation</dt>
                <dd>
                  {vote.legislationUrl ? (
                    <a href={vote.legislationUrl} target="_blank" rel="noreferrer">
                      {legislationLabel(vote)}
                    </a>
                  ) : (
                    legislationLabel(vote)
                  )}
                </dd>
              </div>
              <div>
                <dt>Congress</dt>
                <dd>{vote.congress}</dd>
              </div>
            </dl>
            <ul className="tallies">
              {tallies.map(([cast, count]) => (
                <li key={cast}>
                  <strong>{count}</strong> {cast}
                </li>
              ))}
            </ul>
            <h2>Positions</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Member</th>
                    <th>Vote</th>
                  </tr>
                </thead>
                <tbody>
                  {(vote.positions || []).map((position, index) => (
                    <tr key={`${position.bioguide_id}-${index}`}>
                      <td>
                        <Link to={`/members/${position.bioguide_id}/${vote.congress}`}>
                          {position.name || position.bioguide_id}
                        </Link>
                      </td>
                      <td>{position.vote_cast}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="page-head">
              <h2>Legislation text</h2>
              {text ? (
                vote.summary ? (
                  <button type="button" onClick={openExistingSummary}>
                    View summary
                  </button>
                ) : (
                  <button type="button" disabled={summarizing} onClick={startSummarize}>
                    {summarizing ? 'Summarizing…' : 'Summarize'}
                  </button>
                )
              ) : null}
            </div>
            {text ? (
              <div className="bill-text">
                <p className="muted">
                  {text.version_type} · {formatDate(text.version_date)} · {text.package_id}
                </p>
                <pre>{text.full_text}</pre>
              </div>
            ) : (
              <p className="muted">No bill text for this vote.</p>
            )}
            {modalOpen && (
              <div
                className="modal-backdrop"
                onClick={() => {
                  if (!summarizing) setModalOpen(false)
                }}
              >
                <div className="modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
                  <div className="page-head">
                    <h2>Bill summary</h2>
                    <button type="button" onClick={() => setModalOpen(false)} disabled={summarizing}>
                      Close
                    </button>
                  </div>
                  {summarizing && streamStatus && <p className="muted">{streamStatus}</p>}
                  {summaryError && <p className="status error">{summaryError}</p>}
                  {(summarizing ? draft : vote.summary) && (
                    <div className={`summary-body${summarizing ? ' streaming' : ''}`}>
                      {summarizing ? draft : vote.summary}
                    </div>
                  )}
                  {summarizing && !draft && <p className="status">Waiting for the first tokens…</p>}
                </div>
              </div>
            )}
          </>
        )}
      </Status>
    </section>
  )
}
