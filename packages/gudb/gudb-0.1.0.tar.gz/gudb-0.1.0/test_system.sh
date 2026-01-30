#!/bin/bash

echo "🛡️  AI-DB-Sentinel Test Script"
echo "================================"
echo ""

# Check if server is running
echo "1️⃣  Checking if server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running. Please start it with: uvicorn main:app --reload"
    exit 1
fi

echo ""
echo "2️⃣  Triggering slow query..."
curl -s http://localhost:8000/test/slow
echo ""
echo "✅ Slow query triggered (600ms)"

echo ""
echo "3️⃣  Waiting for analysis to complete..."
sleep 2

echo ""
echo "4️⃣  Fetching alerts..."
ALERTS=$(curl -s http://localhost:8000/api/alerts)
echo "$ALERTS" | python3 -m json.tool

echo ""
echo "5️⃣  Getting service info..."
INFO=$(curl -s http://localhost:8000/)
echo "$INFO" | python3 -m json.tool

echo ""
echo "================================"
echo "✅ Test complete!"
echo ""
echo "📊 View the dashboard at: http://localhost:8000/dashboard"
echo "📚 View API docs at: http://localhost:8000/docs"
echo ""
