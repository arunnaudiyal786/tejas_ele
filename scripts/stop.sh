#!/bin/bash
# Stop the Long-Running Query Manager

set -e

echo "🛑 Stopping Long-Running Query Manager..."

# Stop all services
docker-compose down

# Optional: Remove volumes (uncomment if you want to reset data)
# echo "🗑️  Removing data volumes..."
# docker-compose down -v

echo "✅ All services stopped"
echo ""
echo "💡 To start again: ./scripts/start.sh"
echo "💡 To view stopped containers: docker-compose ps -a"
echo "💡 To remove everything including volumes: docker-compose down -v"