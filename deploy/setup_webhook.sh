#!/bin/bash
# Helper script to set up webhook with ngrok

echo "🔧 Setting up webhook for local development..."
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server is not running on port 8000"
    echo "   Please start it first: uvicorn src.api.main:app --reload --port 8000"
    exit 1
fi

echo "✅ Server is running on port 8000"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo "   Install it with: brew install ngrok"
    echo "   Or download from: https://ngrok.com/download"
    exit 1
fi

echo "✅ ngrok is installed"
echo ""

# Check if ngrok is already running
if pgrep -f "ngrok http 8000" > /dev/null; then
    echo "⚠️  ngrok is already running for port 8000"
    echo "   Getting current URL..."
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "$NGROK_URL" ]; then
        echo "   Current URL: $NGROK_URL"
        WEBHOOK_URL="${NGROK_URL}/api/sms/webhook"
        echo ""
        echo "📋 Webhook URL to configure in Telnyx:"
        echo "   $WEBHOOK_URL"
        echo ""
        echo "To configure in Telnyx:"
        echo "1. Go to https://portal.telnyx.com/"
        echo "2. Navigate to your phone number: +18334209112"
        echo "3. Find 'Messaging' or 'Webhook' settings"
        echo "4. Set webhook URL to: $WEBHOOK_URL"
        echo "5. Save settings"
    fi
else
    echo "🚀 Starting ngrok..."
    echo ""
    echo "This will start ngrok in the background."
    echo "After it starts, you'll see the webhook URL."
    echo ""
    
    # Start ngrok in background
    ngrok http 8000 > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    
    # Wait a moment for ngrok to start
    sleep 3
    
    # Get the URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -n "$NGROK_URL" ]; then
        WEBHOOK_URL="${NGROK_URL}/api/sms/webhook"
        echo "✅ ngrok started!"
        echo ""
        echo "📋 Webhook URL to configure in Telnyx:"
        echo "   $WEBHOOK_URL"
        echo ""
        echo "To configure in Telnyx:"
        echo "1. Go to https://portal.telnyx.com/"
        echo "2. Navigate to your phone number: +18334209112"
        echo "3. Find 'Messaging' or 'Webhook' settings"
        echo "4. Set webhook URL to: $WEBHOOK_URL"
        echo "5. Save settings"
        echo ""
        echo "⚠️  Keep this terminal open - ngrok will stop if you close it"
        echo "   To stop ngrok: kill $NGROK_PID"
        echo ""
        echo "💡 You can also view ngrok dashboard at: http://localhost:4040"
    else
        echo "⚠️  ngrok started but couldn't get URL yet"
        echo "   Check ngrok dashboard: http://localhost:4040"
        echo "   Or wait a few seconds and run this script again"
    fi
fi


