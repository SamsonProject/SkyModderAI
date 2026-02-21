#!/bin/bash
set -e  # Exit on error

echo "🚀 Setting up SkyModderAI development environment..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11 or higher is required. Please install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "❌ Python 3.11 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

echo "🐍 Found Python $PYTHON_VERSION"

# Create and activate virtual environment
echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install requirements
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔒 Creating .env file from template..."
    cp .env.example .env

    # Generate a secure secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Update the .env file with the generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|your-secret-key-here|$SECRET_KEY|" .env
    else
        # Linux/Unix
        sed -i "s|your-secret-key-here|$SECRET_KEY|" .env
    fi

    echo "✅ .env file created with a secure secret key"
else
    echo "ℹ️ .env file already exists"
fi

# Initialize the database
echo "💾 Initializing database..."
if [ ! -f "instance/site.db" ]; then
    python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database tables created')
"
else
    echo "ℹ️ Database already exists"
fi

# Parse LOOT data
echo "🔍 Parsing LOOT masterlist data..."
python3 loot_parser.py skyrimse

echo "✨ Setup complete!"
echo "\nTo start the development server, run:"
echo "  source venv/bin/activate  # Activate virtual environment"
echo "  flask run --host=0.0.0.0 --port=10000 --debug"
echo "\nThen open http://localhost:10000 in your browser"
