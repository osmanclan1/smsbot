# UI Upgrade Guide - Tailwind CSS + Vite

## Overview

The admin dashboard has been upgraded to use **Tailwind CSS** with **Vite** build tooling for a modern, maintainable, and professional UI.

## What Changed

### New Structure
```
admin/
├── src/              # Source files (develop here)
│   ├── index.html    # Main dashboard
│   ├── login.html    # Login page
│   ├── js/           # JavaScript files
│   └── styles/       # CSS files (Tailwind)
└── dist/             # Built files (auto-generated, served by FastAPI)
```

### Technology Stack
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool and dev server
- **PostCSS** - CSS processing
- **Autoprefixer** - Browser compatibility

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

This installs:
- vite
- tailwindcss
- postcss
- autoprefixer

### 2. Development Workflow

**Option A: Use Vite Dev Server (Recommended for Development)**
```bash
# Terminal 1: Start FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Start Vite dev server (with hot reload)
npm run dev
```

Then access:
- Frontend: http://localhost:3000/admin
- Backend API: http://localhost:8000/api

Vite dev server proxies `/api` requests to FastAPI automatically.

**Option B: Build and Serve via FastAPI**
```bash
# Build for production
npm run build

# Start FastAPI (serves built files from admin/dist)
uvicorn src.api.main:app --reload --port 8000
```

Then access:
- Dashboard: http://localhost:8000/admin

### 3. Production Build

```bash
npm run build
```

This creates optimized files in `admin/dist/` that FastAPI serves automatically.

## Key Features

### Modern Design System
- **Custom color palette** - Primary/secondary gradients
- **Dark mode** - Automatic dark mode support
- **Responsive** - Mobile-first design
- **Animations** - Smooth transitions and effects

### Improved Components
- **Header** - Gradient background with glassmorphism
- **Cards** - Modern shadows and borders
- **Forms** - Better focus states and validation
- **Buttons** - Gradient styles with hover effects
- **Chat UI** - Better message bubbles and layout
- **Modals** - Smooth animations and backdrop blur

### Better UX
- **Tab navigation** - Clear active states
- **Status messages** - Color-coded alerts
- **Loading states** - Better feedback
- **Error handling** - User-friendly error messages

## Dark Mode

Dark mode is automatically supported and persists via localStorage. Users can toggle it using the theme button in the header.

## Customization

### Colors
Edit `tailwind.config.js` to customize:
- Primary colors (gradient start)
- Secondary colors (gradient end)
- Custom theme colors

### Components
All components use Tailwind utility classes. Customize by editing:
- `admin/src/index.html` - Dashboard layout
- `admin/src/login.html` - Login page
- `admin/src/js/dashboard.js` - JavaScript behavior

## Migration Notes

- Old files in `admin/` (index.html, login.html, dashboard.js, styles.css) are kept for reference
- New files are in `admin/src/`
- FastAPI automatically serves from `admin/dist/` if it exists, otherwise falls back to `admin/src/`

## Troubleshooting

**Issue: Styles not loading**
- Make sure you ran `npm run build` if using FastAPI directly
- Check browser console for errors

**Issue: API calls failing**
- Make sure FastAPI is running on port 8000
- Check Vite proxy configuration in `vite.config.js`

**Issue: Dark mode not working**
- Check that `dark` class is being toggled on `<html>` element
- Verify localStorage has `theme` key

## Next Steps

- Consider migrating to React if you need more complex state management
- Add more components as needed
- Customize colors to match your brand
- Add more animations and interactions
