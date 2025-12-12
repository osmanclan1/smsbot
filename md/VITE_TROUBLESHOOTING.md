# Vite Dev Server Troubleshooting

## HMR Ping Failures (Status 0)

If you're seeing `ERR_CONNECTION_REFUSED` or status 0 errors for Vite HMR ping requests:

### 1. Verify Vite Server is Running

```bash
# Check if Vite is running on port 3000
lsof -i :3000

# Or check with netstat
netstat -an | grep 3000
```

### 2. Start Vite Dev Server

```bash
npm run dev
```

You should see output like:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 3. Check for Port Conflicts

If port 3000 is already in use:

```bash
# Find what's using port 3000
lsof -i :3000

# Kill the process (replace PID)
kill -9 <PID>
```

### 4. Browser Console Errors

Open browser DevTools (F12) and check:
- **Console tab**: Look for HMR-related errors
- **Network tab**: Check if requests to `/@vite/client` are successful

### 5. Clear Browser Cache

Sometimes stale service workers or cached files cause issues:

```bash
# Hard refresh in browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# Or clear cache completely
# Chrome: Settings → Privacy → Clear browsing data
```

### 6. Check Vite Configuration

Ensure `vite.config.js` has proper HMR settings (already configured):
- `server.hmr.protocol: 'ws'`
- `server.hmr.host: 'localhost'`
- `server.hmr.port: 3000`

### 7. Firewall/Antivirus

Some firewalls or antivirus software block WebSocket connections:

- Temporarily disable to test
- Add exception for `localhost:3000`
- Allow Node.js/Node processes

### 8. Network Extensions

Browser extensions (especially ad blockers, privacy tools) can interfere:

- Try incognito/private mode
- Disable extensions one by one
- Test in different browser

### 9. Restart Everything

Sometimes a clean restart fixes issues:

```bash
# Stop Vite (Ctrl+C)
# Kill any remaining Node processes
pkill -f vite
pkill -f node

# Clear npm cache (optional)
npm cache clean --force

# Restart
npm run dev
```

### 10. Check Node Version

Ensure you're using a compatible Node.js version:

```bash
node --version
# Should be 18.x or 20.x

# If outdated, use nvm to update
nvm install 20
nvm use 20
```

## Expected Behavior

When working correctly:
- ✅ Vite server runs on `http://localhost:3000`
- ✅ HMR WebSocket connects automatically
- ✅ Changes to files trigger hot reload
- ✅ No connection refused errors in console

## Common Error Messages

**"Failed to fetch dynamically imported module"**
- Usually means server restarted or file changed
- Refresh the page

**"WebSocket connection failed"**
- Server not running or port blocked
- Check server status

**"HMR ping failed" (Status 0)**
- Server not accessible
- Check if `npm run dev` is running
- Verify port 3000 is open
