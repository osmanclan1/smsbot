#!/bin/bash
# Fix Vite white page / 404 errors

echo "🔧 Fixing Vite issues..."

# Kill any running Vite processes
echo "1. Stopping any running Vite processes..."
pkill -f "vite" 2>/dev/null || echo "   No Vite processes found"

# Clear Vite cache
echo "2. Clearing Vite cache..."
rm -rf node_modules/.vite
rm -rf admin/.vite 2>/dev/null
rm -rf student/.vite 2>/dev/null
rm -rf .vite 2>/dev/null

# Clear build directories
echo "3. Clearing build directories..."
rm -rf admin/dist
rm -rf student/dist

# Clear npm cache (optional but can help)
echo "4. Clearing npm cache..."
npm cache clean --force

# Reinstall dependencies if needed (uncomment if issues persist)
# echo "5. Reinstalling dependencies..."
# rm -rf node_modules package-lock.json
# npm install

echo ""
echo "✅ Done! Now try running:"
echo "   npm run dev"
echo ""
echo "If you still see issues, try:"
echo "   1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)"
echo "   2. Clear browser cache"
echo "   3. Try incognito/private mode"



