export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function districtLabel(member) {
  if (member.district != null) return `${member.stateCode}-${member.district}`
  if (!member.stateCode) return '—'
  // Senators represent a whole state, so "at-large" only makes sense in the House.
  if (member.chamber === 'Senate') return member.stateCode
  return `${member.stateCode} at-large`
}

export function partyClass(party) {
  const value = (party || '').toLowerCase()
  if (value.startsWith('rep')) return 'party-r'
  if (value.startsWith('dem')) return 'party-d'
  if (value.startsWith('ind')) return 'party-i'
  return 'party-other'
}

export function legislationLabel(vote) {
  if (!vote.legislationType || !vote.legislationNumber) return '—'
  return `${vote.legislationType} ${vote.legislationNumber}`
}
