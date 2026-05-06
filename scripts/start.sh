#!/bin/bash
# NexaFlow Quick Start
set -e

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${BLUE}"
echo "  ███╗   ██╗███████╗██╗  ██╗ █████╗ ███████╗██╗      ██████╗ ██╗    ██╗"
echo "  ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔════╝██║     ██╔═══██╗██║    ██║"
echo "  ██╔██╗ ██║█████╗   ╚███╔╝ ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║"
echo "  ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║"
echo "  ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝"
echo "  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝"
echo -e "${NC}"
echo -e "${GREEN}AI-Powered Code Review Platform${NC}"
echo ""

if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
  echo -e "${YELLOW}Docker found — using Docker Compose...${NC}"
  docker-compose up -d
  echo ""
  echo -e "${GREEN}✅ NexaFlow is running!${NC}"
  echo "  Frontend  → http://localhost"
  echo "  API       → http://`${import.meta.env.VITE_API_URL}`"
  echo "  API Docs  → http://`${import.meta.env.VITE_API_URL}`/api/docs"
  echo ""
  echo "  Login: alex / alex123  or  demo / demo123"
else
  echo -e "${YELLOW}Starting in dev mode...${NC}"
  cd backend
  [ ! -d venv ] && python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt -q
  [ ! -f .env ] && cp .env.example .env
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
  BACK_PID=$!
  cd ../frontend
  [ ! -d node_modules ] && npm install -q
  [ ! -f .env ] && cp .env.example .env
  npm run dev &
  FRONT_PID=$!
  echo ""
  echo -e "${GREEN}✅ NexaFlow is running!${NC}"
  echo "  Frontend  → http://localhost:5173"
  echo "  API       → http://`${import.meta.env.VITE_API_URL}`"
  echo ""
  echo "  Login: alex / alex123  or  demo / demo123"
  echo ""
  echo "Press Ctrl+C to stop."
  wait $BACK_PID $FRONT_PID
fi
