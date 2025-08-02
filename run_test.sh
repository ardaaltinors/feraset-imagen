#!/bin/bash

echo "🧪 Firebase Functions Async API Test Runner"
echo "==========================================="

# Check if emulator is running
if ! curl -s "http://127.0.0.1:5551" > /dev/null; then
    echo "❌ Firebase emulator is not running!"
    echo "📝 Please start it first with: firebase emulators:start"
    exit 1
fi

echo "✅ Firebase emulator detected"

# Check if database is seeded
echo "🌱 Seeding database with test data..."
curl -s -X POST "http://127.0.0.1:5551/feraset-imagen/us-central1/seed_database" | grep -q '"success":true'

if [ $? -eq 0 ]; then
    echo "✅ Database seeded successfully"
else
    echo "⚠️  Database seeding may have failed, continuing anyway..."
fi

echo ""
echo "🚀 Running async API tests..."
echo ""

# Run the test script
python test_async_api.py

echo ""
echo "🏁 Test run completed!"