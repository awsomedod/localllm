export default function Pagination({ offset, limit, count, onPage }) {
  const start = count === 0 ? 0 : offset + 1
  const end = Math.min(offset + limit, count)
  return (
    <div className="pagination">
      <button type="button" disabled={offset <= 0} onClick={() => onPage(Math.max(0, offset - limit))}>
        Previous
      </button>
      <span>
        {start}–{end} of {count.toLocaleString()}
      </span>
      <button type="button" disabled={offset + limit >= count} onClick={() => onPage(offset + limit)}>
        Next
      </button>
    </div>
  )
}
