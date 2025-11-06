#!/bin/bash

echo "Testing semantic search in web UI..."
echo ""

# Start server in background
./venv/bin/python3 main.py --markdown --port 8001 > /tmp/server.log 2>&1 &
SERVER_PID=$!

echo "Server started (PID: $SERVER_PID)"
echo "Waiting for server to be ready..."

# Wait for server to start
sleep 8

# Test API endpoint
echo ""
echo "Testing /api/analyze with 'authentication tokens'..."
curl -s http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"authentication tokens"}' \
  | python3 -m json.tool > /tmp/api_response.json

# Check if semantic_matches exist
if grep -q "semantic_matches" /tmp/api_response.json; then
    echo "✓ Semantic matches found in response!"
    echo ""
    echo "Semantic matches:"
    cat /tmp/api_response.json | python3 -c "import sys, json; data = json.load(sys.stdin); print(json.dumps(data.get('semantic_matches', []), indent=2))"
else
    echo "❌ No semantic matches in response"
    echo ""
    echo "Full response:"
    cat /tmp/api_response.json
fi

echo ""
echo "Server log:"
tail -30 /tmp/server.log

# Kill server
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "Test complete"
