#!/bin/bash
# Start the Long-Running Query Manager with Docker Compose

set -e

echo "🚀 Starting Long-Running Query Manager with CrewAI"
echo "=" * 60

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.docker .env
    echo "📝 Please edit .env file with your OpenAI API key and other settings"
    echo "🔑 IMPORTANT: Add your OpenAI API key to .env file before continuing!"
    read -p "Press Enter after updating .env file..."
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "❌ Please update OPENAI_API_KEY in .env file with your actual API key"
    exit 1
fi

# Create necessary directories
mkdir -p logs data

# Start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Initialize database
echo "🗄️  Initializing database with sample data..."
docker-compose exec app python app/setup_db.py

echo "✅ System is starting up!"
echo ""
echo "🌐 Access points:"
echo "   • Web Interface: http://localhost:8000"
echo "   • AI Agents: http://localhost:8000/agents"
echo "   • Tickets: http://localhost:8000/tickets"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Optional monitoring (if enabled):"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "🔍 To view logs: docker-compose logs -f [service_name]"
echo "🛑 To stop: docker-compose down"