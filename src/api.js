const BASE = '/kinhdich'

export function getUserId() {
  let id = localStorage.getItem('kd_user_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('kd_user_id', id)
  }
  return id
}

// Gắn danh tính khi đăng nhập (Google/FB/user) — tiến độ học sẽ theo id này.
export function setActiveUser(uid) {
  localStorage.setItem('kd_user_id', uid)
}

// Đăng xuất → quay lại danh tính khách (uuid mới), tiến độ tách khỏi tài khoản.
export function clearActiveUser() {
  const guest = crypto.randomUUID()
  localStorage.setItem('kd_user_id', guest)
  localStorage.removeItem('kd_token')
  return guest
}

// Admin: danh sách user (gửi token qua header)
export async function listUsers() {
  const res = await fetch(`${BASE}/users`, {
    headers: { 'x-kd-token': localStorage.getItem('kd_token') || '' },
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Không tải được danh sách user')
  return data.users
}

export async function registerUser(username, password) {
  const res = await fetch(`${BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Đăng ký thất bại')
  return data // { username, isAdmin }
}

export async function loginUser(username, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Đăng nhập thất bại')
  return data // { username, isAdmin }
}

// ---- Learning Lens (profile) ----
export async function fetchProfile() {
  const res = await fetch(`${BASE}/profile/${getUserId()}`)
  if (!res.ok) throw new Error('Lỗi tải hồ sơ')
  return res.json() // { userId, learningLens }
}
export async function saveLens(learningLens) {
  const res = await fetch(`${BASE}/profile/${getUserId()}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ learningLens }),
  })
  if (!res.ok) throw new Error('Lỗi lưu góc nhìn')
  return res.json()
}

// ---- Reflection ----
export async function saveReflection(day, content) {
  const res = await fetch(`${BASE}/reflections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId: getUserId(), day, content }),
  })
  if (!res.ok) throw new Error('Lỗi lưu suy ngẫm')
  return res.json()
}
export async function fetchReflections() {
  const res = await fetch(`${BASE}/reflections/${getUserId()}`)
  if (!res.ok) throw new Error('Lỗi tải suy ngẫm')
  return res.json()
}

// ---- Daily Observation ----
export async function fetchTodayObservation() {
  const res = await fetch(`${BASE}/observations/${getUserId()}/today`)
  if (!res.ok) throw new Error('Lỗi tải quan sát')
  return res.json()
}
export async function fetchObservations() {
  const res = await fetch(`${BASE}/observations/${getUserId()}`)
  if (!res.ok) throw new Error('Lỗi tải quan sát')
  return res.json()
}
export async function saveObservation({ growing, declining, transforming }) {
  const res = await fetch(`${BASE}/observations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId: getUserId(), growing, declining, transforming }),
  })
  if (!res.ok) throw new Error('Lỗi lưu quan sát')
  return res.json()
}

// ---- Case Study ----
export async function fetchCases() {
  const res = await fetch(`${BASE}/cases`)
  if (!res.ok) throw new Error('Lỗi tải tình huống')
  return res.json()
}
export async function fetchCase(id) {
  const res = await fetch(`${BASE}/cases/${id}`)
  if (!res.ok) throw new Error('Không tìm thấy tình huống')
  return res.json()
}

export async function fetchLessons() {
  const res = await fetch(`${BASE}/lessons`)
  if (!res.ok) throw new Error('Không kết nối được backend')
  return res.json()
}

export async function fetchLesson(day) {
  const res = await fetch(`${BASE}/lessons/${day}`)
  if (!res.ok) throw new Error('Không tìm thấy bài học')
  return res.json()
}

export async function fetchProgress() {
  const userId = getUserId()
  const res = await fetch(`${BASE}/progress/${userId}`)
  if (!res.ok) throw new Error('Lỗi tải tiến độ')
  return res.json()
}

export async function markComplete(day, score) {
  const userId = getUserId()
  const res = await fetch(`${BASE}/progress`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, day, score }),
  })
  if (!res.ok) throw new Error('Lỗi lưu tiến độ')
  return res.json()
}

export async function* streamTutor(message, history = [], mode = 'explain') {
  const userId = getUserId()
  const res = await fetch(`${BASE}/tutor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, message, history, mode }),
  })
  if (!res.ok) throw new Error('Lỗi kết nối AI Tutor')
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data && data !== '[DONE]') {
          try {
            const parsed = JSON.parse(data)
            if (parsed.text) yield parsed.text
          } catch {}
        }
      }
    }
  }
}
