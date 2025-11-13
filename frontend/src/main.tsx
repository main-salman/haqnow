import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppWrapper } from './AppWrapper.tsx'
import './index.css'
// Polyfill for support react use in react 18
import "./polyfills/react-polyfill";

// Handle chunk loading errors (when new deployment happens while user has site open)
// Automatically reload the page to fetch the new chunks
window.addEventListener('error', (event) => {
  const isChunkLoadError = 
    event.message.includes('Failed to fetch dynamically imported module') ||
    event.message.includes('Importing a module script failed') ||
    (event.target instanceof HTMLScriptElement && event.target.src);
  
  if (isChunkLoadError) {
    console.warn('Chunk loading failed, reloading page to fetch updated assets...');
    // Add a flag to prevent infinite reload loops
    const reloadedKey = 'app-reloaded';
    const hasReloaded = sessionStorage.getItem(reloadedKey);
    
    if (!hasReloaded) {
      sessionStorage.setItem(reloadedKey, 'true');
      window.location.reload();
    } else {
      // If already reloaded once, clear the flag and show error
      sessionStorage.removeItem(reloadedKey);
      console.error('Chunk loading failed after reload. Manual refresh may be needed.');
    }
  }
});

// Clear the reload flag on successful load
window.addEventListener('load', () => {
  sessionStorage.removeItem('app-reloaded');
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppWrapper />
  </StrictMode>,
)
