// API configuration
// In production, use environment variable or Lambda API Gateway URL
// In development, use localhost or same origin
const getApiBase = () => {
  // Check for environment variable first (set in Vercel/Amplify)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // If deployed on Vercel, use Lambda API Gateway URL
  if (window.location.origin.includes('vercel.app') || window.location.origin.includes('vercel.com')) {
    return 'https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod'
  }
  
  // If deployed on Amplify, use Lambda API Gateway URL
  if (window.location.origin.includes('amplify.app')) {
    return 'https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod'
  }
  
  // Development fallback
  return window.location.origin.replace('/admin', '') || 'http://localhost:8000'
}

export const API_BASE = getApiBase()

