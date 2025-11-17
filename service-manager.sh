#!/bin/bash

# AI-ClaimLite Service Manager
# Quick script untuk manage services

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/shunkazama/Documents/Kerja/AI-ClaimLite"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI-ClaimLite Service Manager v1.0   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to check if core_engine is running
check_core_engine() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Core Engine: ${GREEN}Running${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} Core Engine: ${RED}Not Running${NC}"
        return 1
    fi
}

# Function to check if backend is running
check_backend() {
    if curl -s http://localhost:3001/api/auth/me > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend: ${GREEN}Running${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} Backend: ${RED}Not Running${NC}"
        return 1
    fi
}

# Function to check if database is running
check_database() {
    if sudo systemctl is-active --quiet postgresql 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Database: ${GREEN}Running${NC}"
        return 0
    elif sudo docker ps | grep -q postgres 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Database (Docker): ${GREEN}Running${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} Database: ${RED}Not Running${NC}"
        return 1
    fi
}

# Function to start core_engine
start_core_engine() {
    echo -e "${YELLOW}Starting Core Engine...${NC}"
    cd "$PROJECT_DIR/core_engine"
    
    # Kill existing process
    sudo pkill -f "python main.py" 2>/dev/null
    sleep 2
    
    # Start new process
    nohup python main.py > logs/core.log 2>&1 &
    sleep 5
    
    if check_core_engine; then
        echo -e "${GREEN}Core Engine started successfully!${NC}"
    else
        echo -e "${RED}Failed to start Core Engine. Check logs/core.log${NC}"
    fi
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Backend...${NC}"
    cd "$PROJECT_DIR/web"
    
    # Kill existing process
    sudo pkill -f "vite.*preview" 2>/dev/null
    sudo pkill -f "node.*server" 2>/dev/null
    sleep 2
    
    # Start new process
    nohup npm run dev > logs/backend.log 2>&1 &
    sleep 10
    
    if check_backend; then
        echo -e "${GREEN}Backend started successfully!${NC}"
    else
        echo -e "${RED}Failed to start Backend. Check logs/backend.log${NC}"
    fi
}

# Function to stop all services
stop_all() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    sudo pkill -f "python main.py" 2>/dev/null
    sudo pkill -f "vite.*preview" 2>/dev/null
    sudo pkill -f "node.*server" 2>/dev/null
    sleep 2
    echo -e "${GREEN}All services stopped${NC}"
}

# Function to restart all services
restart_all() {
    echo -e "${YELLOW}Restarting all services...${NC}"
    stop_all
    echo ""
    start_core_engine
    echo ""
    start_backend
}

# Function to show status
show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    echo "─────────────────────────────────────────"
    check_core_engine
    check_backend
    check_database
    echo "─────────────────────────────────────────"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}Recent Logs:${NC}"
    echo ""
    echo -e "${YELLOW}Core Engine (last 20 lines):${NC}"
    tail -20 "$PROJECT_DIR/core_engine/logs/app.log" 2>/dev/null || echo "No logs found"
    echo ""
    echo -e "${YELLOW}Backend (last 20 lines):${NC}"
    tail -20 "$PROJECT_DIR/web/logs/backend.log" 2>/dev/null || echo "No logs found"
}

# Function to run diagnostics
run_diagnostics() {
    echo -e "${BLUE}Running Diagnostics...${NC}"
    echo "─────────────────────────────────────────"
    
    echo -n "1. Core Engine Health: "
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo -n "2. Backend API: "
    if curl -s http://localhost:3001/api/auth/me > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo -n "3. Database: "
    if check_database > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo -n "4. OpenAI API Key: "
    if grep -q "OPENAI_API_KEY=sk-" "$PROJECT_DIR/core_engine/.env" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}NOT FOUND${NC}"
    fi
    
    echo -n "5. Disk Space: "
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "${GREEN}OK ($DISK_USAGE%)${NC}"
    else
        echo -e "${YELLOW}WARNING ($DISK_USAGE%)${NC}"
    fi
    
    echo -n "6. Internet (OpenAI): "
    if ping -c 1 api.openai.com > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
    
    echo "─────────────────────────────────────────"
}

# Main menu
case "$1" in
    status)
        show_status
        ;;
    start)
        case "$2" in
            core)
                start_core_engine
                ;;
            backend)
                start_backend
                ;;
            all)
                restart_all
                ;;
            *)
                echo "Usage: $0 start {core|backend|all}"
                ;;
        esac
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    logs)
        show_logs
        ;;
    diagnostics|test)
        run_diagnostics
        ;;
    *)
        echo "AI-ClaimLite Service Manager"
        echo ""
        echo "Usage: $0 {status|start|stop|restart|logs|diagnostics}"
        echo ""
        echo "Commands:"
        echo "  status        - Show service status"
        echo "  start all     - Start all services"
        echo "  start core    - Start core engine only"
        echo "  start backend - Start backend only"
        echo "  stop          - Stop all services"
        echo "  restart       - Restart all services"
        echo "  logs          - Show recent logs"
        echo "  diagnostics   - Run diagnostic tests"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 restart"
        echo "  $0 start core"
        echo "  $0 diagnostics"
        ;;
esac
