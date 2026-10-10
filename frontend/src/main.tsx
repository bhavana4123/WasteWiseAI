import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Routes from './Routes'
import './styles.css'
createRoot(document.getElementById('root')!).render(<StrictMode><Routes /></StrictMode>)
