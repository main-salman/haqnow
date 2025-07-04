import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppWrapper } from './AppWrapper.tsx'
import './index.css'
// Polyfill for support react use in react 18
import "./polyfills/react-polyfill";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppWrapper />
  </StrictMode>,
)
