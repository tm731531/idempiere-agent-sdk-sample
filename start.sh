#!/bin/bash

# iDempiere Agent SDK - Quick Start Script

echo "🚀 Starting iDempiere Agent SDK..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q flask anthropic psycopg2-binary python-dotenv

# Check environment variables
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << 'EOF'
# iDempiere Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=idempiere
DB_USER=adempiere
DB_PASSWORD=adempiere

# Claude API Configuration
ANTHROPIC_API_KEY=your_api_key_here
EOF
    echo "📝 Please edit .env and add your ANTHROPIC_API_KEY"
    echo ""
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Test database connection
echo "🔗 Testing database connection..."
python3 -c "
import sys
sys.path.insert(0, '.')
from tools.database import DatabaseTool

db = DatabaseTool()
try:
    db.connect()
    count = db._execute_query('SELECT COUNT(*) as cnt FROM adempiere.c_order', [])
    if count:
        print(f'✅ Database connected! ({count[0][\"cnt\"]} orders in system)')
    else:
        print('✅ Database connected!')
    db.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" || exit 1

echo ""
echo "🌐 Starting Flask application..."
echo "📋 Available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Flask app
python3 app.py
