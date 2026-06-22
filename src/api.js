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
  return guest
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

export async function* streamTutor(message, history = []) {
  const userId = getUserId()
  const res = await fetch(`${BASE}/tutor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, message, history }),
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
