import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getMember } from '../api'
import Status from '../components/Status'
import { districtLabel, partyClass } from '../format'

export default function MemberDetailPage() {
  const { bioguideId, congress } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [member, setMember] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    getMember(bioguideId, congress, controller.signal)
      .then((payload) => {
        setMember(payload)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(err.message)
        setLoading(false)
      })
    return () => controller.abort()
  }, [bioguideId, congress])

  return (
    <section>
      <p className="crumb">
        <Link to="/">Members</Link>
      </p>
      <Status loading={loading} error={error}>
        {member && (
          <div className="detail">
            <img className="portrait" src={member.image_url} alt="" />
            <div>
              <p className={`pill ${partyClass(member.party)}`}>{member.party}</p>
              <h1>{member.name}</h1>
              <p className="muted">
                {member.memberType} · {member.chamber} · {districtLabel(member)}
              </p>
              <dl className="facts">
                <div>
                  <dt>Bioguide</dt>
                  <dd>{member.bioguide_id}</dd>
                </div>
                <div>
                  <dt>Congress</dt>
                  <dd>{member.congress}</dd>
                </div>
                <div>
                  <dt>State</dt>
                  <dd>
                    {member.stateName} ({member.stateCode})
                  </dd>
                </div>
                <div>
                  <dt>Service</dt>
                  <dd>
                    {member.startYear}–{member.endYear}
                  </dd>
                </div>
                <div>
                  <dt>Born</dt>
                  <dd>{member.birthYear || '—'}</dd>
                </div>
                <div>
                  <dt>Sponsored</dt>
                  <dd>{member.sponsoredLegislationCount ?? '—'}</dd>
                </div>
                <div>
                  <dt>Cosponsored</dt>
                  <dd>{member.cosponsoredLegislationCount ?? '—'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}
      </Status>
    </section>
  )
}
