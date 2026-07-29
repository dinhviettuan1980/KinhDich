import { initializeApp, getApps, getApp } from 'firebase/app'
import { getAuth, setPersistence, browserLocalPersistence } from 'firebase/auth'

// Same Firebase project already used by ConnectDoctor — shared identity for the whole
// tuandv.id.vn ecosystem, not app-specific. Public web config, safe to embed client-side
// (restricted by Firebase Authorized domains, not by keeping this value secret).
// See .claude/plans/virtual-sparking-beaver.md.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: 'connectdoctor-8d202.firebaseapp.com',
  projectId: 'connectdoctor-8d202',
  storageBucket: 'connectdoctor-8d202.firebasestorage.app',
  messagingSenderId: '1063151091025',
  appId: '1:1063151091025:web:9f7613a32dcfe2d54fa770',
}

export const app = getApps().length ? getApp() : initializeApp(firebaseConfig)
export const auth = getAuth(app)
setPersistence(auth, browserLocalPersistence).catch(() => {})
