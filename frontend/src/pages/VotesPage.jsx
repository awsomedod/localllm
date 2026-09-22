import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listHouseVotes } from '../api'
import Pagination from '../components/Pagination'
import Status from '../components/Status'
import { formatDate, legislationLabel } from '../format'

const PAGE_SIZE = 20

export default function VotesPage() {
  const [congress, setCongress] = useState('118')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState({ items: [], pagination: { count: 0, offset: 0, limit: PAGE_SIZE } })

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    listHouseVotes(
      { congress: congress || undefined, offset, limit: PAGE_SIZE },
      controller.signal,
    )
      .then((payload) => {
        setData(payload)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(err.message)
        setLoading(false)
      })
    return () => controller.abort()
  }, [congress, offset])

  return (
    <section>
      <div className="page-head">
        <h1>House votes</h1>
        <label>
          Congress
          <input
            type="number"
            min="1"
            value={congress}
            onChange={(event) => {
              setCongress(event.target.value)
              setOffset(0)
            }}
          />
        </label>
      </div>
      <Status loading={loading} error={error}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Roll</th>
                <th>Legislation</th>
                <th>Type</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((vote) => (
                <tr key={vote.identifier}>
                  <td>{formatDate(vote.startDate)}</td>
                  <td>
                    <Link to={`/votes/${vote.identifier}`}>
                      S{vote.sessionNumber} #{vote.rollCallNumber}
                    </Link>
                  </td>
                  <td>{legislationLabel(vote)}</td>
                  <td>{vote.voteType}</td>
                  <td>{vote.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination
          offset={data.pagination.offset}
          limit={data.pagination.limit}
          count={data.pagination.count}
          onPage={setOffset}
        />
      </Status>
    </section>
  )
}
