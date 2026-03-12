#!/bin/bash
set -e
echo "========================================"
echo " FinCore Banking Assistant v2 Setup"
echo "========================================"

# Python venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Generate data
echo "Generating mock banking data..."
python data/generate_mock_data.py

# Seed Neo4j
echo "Seeding Neo4j AuraDB knowledge graph..."
python -c "from src.knowledge_graph.seed_data import seed_all; seed_all()"

# Init SQLite audit DB
echo "Initializing SQLite audit database..."
python -c "from src.database.database import init_db; init_db()"

# Fix any unicode issues
echo "Fixing unicode characters in source files..."
python fix_unicode.py

# Frontend
echo "Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo " Start backend:"
echo "   source venv/bin/activate"
echo "   python -m uvicorn src.main:app --reload --port 8000"
echo ""
echo " Start frontend (new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo " Open:"
echo "   Chat:    http://localhost:3000"
echo "   Demo:    http://localhost:3000/demo"
echo "   API:     http://localhost:8000/docs"
echo "========================================"