#!/bin/bash

# HealthConnect AI - Development Server Startup Script
# Production-grade development environment setup
# Version: 1.0.0
# Last Updated: 2025-06-20

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="healthconnect-ai"
FRONTEND_PORT=3000
BACKEND_PORT=8000
WS_PORT=8080
DB_PORT=5432
REDIS_PORT=6379

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if port is available
check_port() {
    local port="$1"
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Kill process on port
kill_port() {
    local port="$1"
    local pid=$(lsof -ti:$port)
    if [[ -n "$pid" ]]; then
        kill -9 $pid
        log "Killed process on port $port"
    fi
}

# Start database services
start_database_services() {
    log "Starting database services..."
    
    # Start PostgreSQL with Docker
    if ! docker ps | grep -q "${PROJECT_NAME}-postgres"; then
        log "Starting PostgreSQL container..."
        docker run -d \
            --name "${PROJECT_NAME}-postgres" \
            -e POSTGRES_DB="${PROJECT_NAME}_dev" \
            -e POSTGRES_USER="${PROJECT_NAME}_user" \
            -e POSTGRES_PASSWORD="dev_password" \
            -p $DB_PORT:5432 \
            -v "${PROJECT_NAME}-postgres-data:/var/lib/postgresql/data" \
            postgres:15-alpine
        
        # Wait for PostgreSQL to be ready
        log "Waiting for PostgreSQL to be ready..."
        sleep 10
        
        # Run database migrations
        cd backend
        python manage.py migrate 2>/dev/null || true
        cd ..
    else
        log "PostgreSQL container already running"
    fi
    
    # Start Redis with Docker
    if ! docker ps | grep -q "${PROJECT_NAME}-redis"; then
        log "Starting Redis container..."
        docker run -d \
            --name "${PROJECT_NAME}-redis" \
            -p $REDIS_PORT:6379 \
            -v "${PROJECT_NAME}-redis-data:/data" \
            redis:7-alpine redis-server --appendonly yes
    else
        log "Redis container already running"
    fi
    
    success "Database services started"
}

# Start backend services
start_backend() {
    log "Starting backend services..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Set environment variables
    export ENVIRONMENT="development"
    export DEBUG="true"
    export DATABASE_URL="postgresql://${PROJECT_NAME}_user:dev_password@localhost:$DB_PORT/${PROJECT_NAME}_dev"
    export REDIS_URL="redis://localhost:$REDIS_PORT/0"
    export JWT_SECRET="dev-secret-key"
    export LOG_LEVEL="debug"
    
    # Run database migrations
    log "Running database migrations..."
    python manage.py migrate
    
    # Create superuser if it doesn't exist
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@healthconnect-ai.com', 'admin123!')
    print('Superuser created: admin/admin123!')
" 2>/dev/null || true
    
    # Start development server
    log "Starting backend development server on port $BACKEND_PORT..."
    python manage.py runserver 0.0.0.0:$BACKEND_PORT &
    BACKEND_PID=$!
    
    # Start WebSocket server
    log "Starting WebSocket server on port $WS_PORT..."
    python manage.py runserver_websocket 0.0.0.0:$WS_PORT &
    WS_PID=$!
    
    cd ..
    success "Backend services started"
}

# Start frontend services
start_frontend() {
    log "Starting frontend services..."
    
    cd frontend
    
    # Install dependencies
    log "Installing frontend dependencies..."
    npm install
    
    # Set environment variables
    export NODE_ENV="development"
    export REACT_APP_API_URL="http://localhost:$BACKEND_PORT"
    export REACT_APP_WS_URL="ws://localhost:$WS_PORT"
    export REACT_APP_ENVIRONMENT="development"
    
    # Start development server
    log "Starting frontend development server on port $FRONTEND_PORT..."
    npm start &
    FRONTEND_PID=$!
    
    cd ..
    success "Frontend services started"
}

# Start monitoring services
start_monitoring() {
    log "Starting monitoring services..."
    
    # Start Prometheus (optional)
    if command -v prometheus &> /dev/null; then
        prometheus --config.file=monitoring/prometheus.yml &
        PROMETHEUS_PID=$!
        log "Prometheus started on port 9090"
    fi
    
    # Start Grafana with Docker (optional)
    if docker --version &> /dev/null; then
        if ! docker ps | grep -q "${PROJECT_NAME}-grafana"; then
            docker run -d \
                --name "${PROJECT_NAME}-grafana" \
                -p 3001:3000 \
                -v "${PROJECT_NAME}-grafana-data:/var/lib/grafana" \
                grafana/grafana:latest
            log "Grafana started on port 3001"
        fi
    fi
    
    success "Monitoring services started"
}

# Setup development data
setup_dev_data() {
    log "Setting up development data..."
    
    # Run database seeding script
    if [[ -f "scripts/setup/seed-database.py" ]]; then
        python3 scripts/setup/seed-database.py --environment development --data-only
    fi
    
    success "Development data setup completed"
}

# Health check all services
health_check() {
    log "Performing health checks..."
    
    local services_healthy=true
    
    # Check PostgreSQL
    if pg_isready -h localhost -p $DB_PORT -U "${PROJECT_NAME}_user" &>/dev/null; then
        success "PostgreSQL is healthy"
    else
        error "PostgreSQL health check failed"
        services_healthy=false
    fi
    
    # Check Redis
    if redis-cli -p $REDIS_PORT ping &>/dev/null; then
        success "Redis is healthy"
    else
        error "Redis health check failed"
        services_healthy=false
    fi
    
    # Check Backend
    sleep 5  # Give backend time to start
    if curl -s -f "http://localhost:$BACKEND_PORT/health" &>/dev/null; then
        success "Backend is healthy"
    else
        error "Backend health check failed"
        services_healthy=false
    fi
    
    # Check Frontend
    sleep 10  # Give frontend time to start
    if curl -s -f "http://localhost:$FRONTEND_PORT" &>/dev/null; then
        success "Frontend is healthy"
    else
        warning "Frontend may still be starting..."
    fi
    
    if [[ "$services_healthy" == "true" ]]; then
        success "All core services are healthy"
    else
        error "Some services failed health checks"
    fi
}

# Display service URLs
display_urls() {
    log "Development environment is ready!"
    echo
    echo "Service URLs:"
    echo "  Frontend:     http://localhost:$FRONTEND_PORT"
    echo "  Backend API:  http://localhost:$BACKEND_PORT"
    echo "  WebSocket:    ws://localhost:$WS_PORT"
    echo "  Database:     postgresql://localhost:$DB_PORT/${PROJECT_NAME}_dev"
    echo "  Redis:        redis://localhost:$REDIS_PORT"
    echo "  Admin Panel:  http://localhost:$BACKEND_PORT/admin"
    echo
    echo "Default Credentials:"
    echo "  Admin User:   admin / admin123!"
    echo "  Test Patient: patient1@healthconnect-ai.com / patient123!"
    echo "  Test Provider: provider1@healthconnect-ai.com / provider123!"
    echo
    echo "Useful Commands:"
    echo "  Stop all:     $0 --stop"
    echo "  Restart:      $0 --restart"
    echo "  Logs:         $0 --logs"
    echo "  Status:       $0 --status"
}

# Stop all services
stop_services() {
    log "Stopping all development services..."
    
    # Kill frontend
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    kill_port $FRONTEND_PORT
    
    # Kill backend
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    kill_port $BACKEND_PORT
    
    # Kill WebSocket server
    if [[ -n "${WS_PID:-}" ]]; then
        kill $WS_PID 2>/dev/null || true
    fi
    kill_port $WS_PORT
    
    # Stop Docker containers
    docker stop "${PROJECT_NAME}-postgres" 2>/dev/null || true
    docker stop "${PROJECT_NAME}-redis" 2>/dev/null || true
    docker stop "${PROJECT_NAME}-grafana" 2>/dev/null || true
    
    # Kill monitoring services
    if [[ -n "${PROMETHEUS_PID:-}" ]]; then
        kill $PROMETHEUS_PID 2>/dev/null || true
    fi
    
    success "All services stopped"
}

# Show service status
show_status() {
    log "Development services status:"
    echo
    
    # Check each service
    local services=(
        "Frontend:$FRONTEND_PORT"
        "Backend:$BACKEND_PORT"
        "WebSocket:$WS_PORT"
        "PostgreSQL:$DB_PORT"
        "Redis:$REDIS_PORT"
    )
    
    for service in "${services[@]}"; do
        local name="${service%:*}"
        local port="${service#*:}"
        
        if check_port "$port"; then
            echo "  $name: $(tput setaf 1)STOPPED$(tput sgr0)"
        else
            echo "  $name: $(tput setaf 2)RUNNING$(tput sgr0) (port $port)"
        fi
    done
    
    echo
    
    # Docker containers
    echo "Docker Containers:"
    docker ps --filter "name=${PROJECT_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No containers running"
}

# Show logs
show_logs() {
    local service="${1:-all}"
    
    case "$service" in
        "frontend")
            tail -f frontend/npm-debug.log 2>/dev/null || echo "No frontend logs available"
            ;;
        "backend")
            tail -f backend/logs/django.log 2>/dev/null || echo "No backend logs available"
            ;;
        "database")
            docker logs -f "${PROJECT_NAME}-postgres" 2>/dev/null || echo "Database container not running"
            ;;
        "redis")
            docker logs -f "${PROJECT_NAME}-redis" 2>/dev/null || echo "Redis container not running"
            ;;
        "all"|*)
            log "Showing all service logs (Ctrl+C to exit)..."
            (
                tail -f frontend/npm-debug.log 2>/dev/null &
                tail -f backend/logs/django.log 2>/dev/null &
                docker logs -f "${PROJECT_NAME}-postgres" 2>/dev/null &
                docker logs -f "${PROJECT_NAME}-redis" 2>/dev/null &
                wait
            )
            ;;
    esac
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    stop_services
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM

# Main function
main() {
    log "Starting HealthConnect AI development environment..."
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check required ports
    local required_ports=($FRONTEND_PORT $BACKEND_PORT $WS_PORT $DB_PORT $REDIS_PORT)
    for port in "${required_ports[@]}"; do
        if ! check_port "$port"; then
            warning "Port $port is already in use"
            read -p "Kill process on port $port? (y/n): " kill_confirm
            if [[ "$kill_confirm" == "y" ]]; then
                kill_port "$port"
            else
                error "Cannot start services with port conflicts"
                exit 1
            fi
        fi
    done
    
    start_database_services
    start_backend
    start_frontend
    
    # Optional monitoring
    if [[ "${START_MONITORING:-false}" == "true" ]]; then
        start_monitoring
    fi
    
    # Optional development data
    if [[ "${SETUP_DEV_DATA:-true}" == "true" ]]; then
        setup_dev_data
    fi
    
    health_check
    display_urls
    
    # Keep script running
    log "Development environment is running. Press Ctrl+C to stop all services."
    while true; do
        sleep 1
    done
}

# Handle command line arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "--stop"|"stop")
        stop_services
        ;;
    "--restart"|"restart")
        stop_services
        sleep 2
        main
        ;;
    "--status"|"status")
        show_status
        ;;
    "--logs"|"logs")
        show_logs "${2:-all}"
        ;;
    "--help"|"-h")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  start (default)    Start all development services"
        echo "  stop              Stop all development services"
        echo "  restart           Restart all development services"
        echo "  status            Show service status"
        echo "  logs [service]    Show logs (all, frontend, backend, database, redis)"
        echo
        echo "Environment Variables:"
        echo "  START_MONITORING   Start monitoring services (default: false)"
        echo "  SETUP_DEV_DATA     Setup development data (default: true)"
        exit 0
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
esac
