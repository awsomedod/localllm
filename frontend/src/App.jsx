import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import MemberDetailPage from './pages/MemberDetailPage'
import MembersPage from './pages/MembersPage'
import VoteDetailPage from './pages/VoteDetailPage'
import VotesPage from './pages/VotesPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<MembersPage />} />
          <Route path="/members/:bioguideId/:congress" element={<MemberDetailPage />} />
          <Route path="/votes" element={<VotesPage />} />
          <Route path="/votes/:identifier" element={<VoteDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
