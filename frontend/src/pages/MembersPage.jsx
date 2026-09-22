import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listMembers } from '../api'
import Pagination from '../components/Pagination'
import Status from '../components/Status'
import { districtLabel, partyClass } from '../format'

const PAGE_SIZE = 20

export default function MembersPage() {
  const [congress, setCongress] = useState('118')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState({ items: [], pagination: { count: 0, offset: 0, limit: PAGE_SIZE } })

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    listMembers(
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
        <h1>Members</h1>
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
        <ul className="member-list">
          {data.items.map((member) => (
            <li key={`${member.bioguide_id}-${member.congress}`}>
              <Link to={`/members/${member.bioguide_id}/${member.congress}`} className="member-row">
                <img src={member.image_url} alt="" width="48" height="60" />
                <div>
                  <strong>{member.name}</strong>
                  <div className="muted">
                    {member.memberType} · {districtLabel(member)}
                  </div>
                </div>
                <span className={`pill ${partyClass(member.party)}`}>{member.party}</span>
              </Link>
            </li>
          ))}
        </ul>
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
