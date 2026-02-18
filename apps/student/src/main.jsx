import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/main.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  console.error('Root element not found!')
  document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: Root element not found!</div>'
} else {
  try {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    )
  } catch (error) {
    console.error('Error rendering app:', error)
    rootElement.innerHTML = `
      <div style="padding: 20px; color: red;">
        <h1>Error loading application</h1>
        <p>${error.message}</p>
        <pre>${error.stack}</pre>
      </div>
    `
  }
}
