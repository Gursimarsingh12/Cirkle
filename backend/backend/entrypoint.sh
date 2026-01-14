#!/bin/bash

echo "🚀 Starting cirkle Twitter-like Recommendation System..."
echo "============================================================"

# Wait for MySQL
echo "⏳ Waiting for MySQL..."
./wait-for-it.sh mysql:3306 --timeout=60 --strict
echo "✅ MySQL is ready"

# Wait for Redis
echo "⏳ Waiting for Redis..."
./wait-for-it.sh redis:6379 --timeout=30 --strict
echo "✅ Redis is ready"

# Start FastAPI server to initialize database
echo "🔧 Starting FastAPI server to initialize database..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level info &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server initialization..."
sleep 3

# Wait for health check to pass
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Only run optimization if this is the first backend instance
# Use a simple file-based lock mechanism
LOCK_FILE="/tmp/cirkle_optimization.lock"
HOSTNAME=$(hostname)

if [ ! -f "$LOCK_FILE" ]; then
    echo "$HOSTNAME" > "$LOCK_FILE"
    LOCK_OWNER=$(cat "$LOCK_FILE")
    
    if [ "$LOCK_OWNER" = "$HOSTNAME" ]; then
        echo "🎯 Running production optimization with recommendation system..."
        python optimize_for_production.py || {
            echo "❌ Production optimization failed with exit code $?"
            echo "⚠️  Attempting to continue with basic setup..."
            
            # Check if data exists
            echo "🔍 Checking if data already exists..."
            python check_data_exists.py
            
            if [ $? -eq 1 ]; then
                echo "📝 No existing data found - generating basic mock data..."
                python src/scripts/generate_mock_data.py || {
                    echo "❌ Mock data generation also failed. Exiting."
                    exit 1
                }
            fi
        }
        
        # Remove lock file after completion
        rm -f "$LOCK_FILE"
    else
        echo "⏳ Another instance is running optimization, waiting..."
        # Wait for optimization to complete
        while [ -f "$LOCK_FILE" ]; do
            sleep 5
        done
    fi
else
    echo "⏳ Another instance is running optimization, waiting..."
    # Wait for optimization to complete
    while [ -f "$LOCK_FILE" ]; do
        sleep 5
    done
fi

echo "🎉 Optimization completed or skipped - server ready!"

# Keep the server running
wait $SERVER_PID
