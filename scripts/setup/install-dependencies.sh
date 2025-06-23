#!/bin/bash

# HealthConnect AI - Dependency Installation Script
# Production-grade dependency installation for all components
# Version: 1.0.0
# Last Updated: 2025-06-20

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
        error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then
        error "Insufficient disk space. Minimum 10GB required."
        exit 1
    fi
    
    # Check memory (minimum 4GB)
    total_memory=$(grep MemTotal /proc/meminfo | awk '{print $2}' 2>/dev/null || echo "4194304")
    if [[ $total_memory -lt 4194304 ]]; then
        warning "Less than 4GB RAM detected. Performance may be affected."
    fi
    
    success "System requirements check passed"
}

# Install Node.js and npm
install_nodejs() {
    log "Installing Node.js and npm..."
    
    if command -v node &> /dev/null; then
        node_version=$(node --version | sed 's/v//')
        if [[ "$(printf '%s\n' "18.0.0" "$node_version" | sort -V | head -n1)" == "18.0.0" ]]; then
            success "Node.js $node_version is already installed"
            return
        fi
    fi
    
    # Install Node.js via NodeSource repository
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install node@20
        else
            error "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
    fi
    
    # Verify installation
    if command -v node &> /dev/null && command -v npm &> /dev/null; then
        success "Node.js $(node --version) and npm $(npm --version) installed successfully"
    else
        error "Failed to install Node.js and npm"
        exit 1
    fi
}

# Install Python and pip
install_python() {
    log "Installing Python and pip..."
    
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | awk '{print $2}')
        if [[ "$(printf '%s\n' "3.9.0" "$python_version" | sort -V | head -n1)" == "3.9.0" ]]; then
            success "Python $python_version is already installed"
            return
        fi
    fi
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv python3-dev
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install python@3.11
        else
            error "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
    fi
    
    # Verify installation
    if command -v python3 &> /dev/null && command -v pip3 &> /dev/null; then
        success "Python $(python3 --version) and pip $(pip3 --version) installed successfully"
    else
        error "Failed to install Python and pip"
        exit 1
    fi
}

# Install Docker
install_docker() {
    log "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        success "Docker $(docker --version) is already installed"
        return
    fi
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Install Docker using official script
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        # Install Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install --cask docker
        else
            error "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
    fi
    
    success "Docker installed successfully. Please log out and log back in to use Docker without sudo."
}

# Install AWS CLI
install_aws_cli() {
    log "Installing AWS CLI..."
    
    if command -v aws &> /dev/null; then
        success "AWS CLI $(aws --version) is already installed"
        return
    fi
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
        sudo installer -pkg AWSCLIV2.pkg -target /
        rm AWSCLIV2.pkg
    fi
    
    # Verify installation
    if command -v aws &> /dev/null; then
        success "AWS CLI $(aws --version) installed successfully"
    else
        error "Failed to install AWS CLI"
        exit 1
    fi
}

# Install Terraform
install_terraform() {
    log "Installing Terraform..."
    
    if command -v terraform &> /dev/null; then
        success "Terraform $(terraform version) is already installed"
        return
    fi
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update && sudo apt-get install terraform
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew tap hashicorp/tap
            brew install hashicorp/tap/terraform
        else
            error "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
    fi
    
    # Verify installation
    if command -v terraform &> /dev/null; then
        success "Terraform $(terraform version) installed successfully"
    else
        error "Failed to install Terraform"
        exit 1
    fi
}

# Install frontend dependencies
install_frontend_dependencies() {
    log "Installing frontend dependencies..."
    
    if [[ -f "frontend/package.json" ]]; then
        cd frontend
        npm ci --production=false
        cd ..
        success "Frontend dependencies installed successfully"
    else
        warning "Frontend package.json not found. Skipping frontend dependencies."
    fi
}

# Install backend dependencies
install_backend_dependencies() {
    log "Installing backend dependencies..."
    
    if [[ -f "backend/requirements.txt" ]]; then
        cd backend
        py -3.10 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        cd ..
        success "Backend dependencies installed successfully"
    else
        warning "Backend requirements.txt not found. Skipping backend dependencies."
    fi
}

# Install development tools
install_dev_tools() {
    log "Installing development tools..."
    
    # Install global npm packages
    npm install -g @aws-amplify/cli typescript ts-node nodemon eslint prettier
    
    # Install Python development tools
    pip3 install --user black flake8 pytest mypy
    
    success "Development tools installed successfully"
}

# Main installation function
main() {
    log "Starting HealthConnect AI dependency installation..."
    
    check_root
    check_system_requirements
    
    install_nodejs
    install_python
    install_docker
    install_aws_cli
    install_terraform
    install_frontend_dependencies
    install_backend_dependencies
    install_dev_tools
    
    success "All dependencies installed successfully!"
    log "Please restart your terminal or run 'source ~/.bashrc' to ensure all tools are available in your PATH."
    
    # Display installed versions
    echo
    log "Installed versions:"
    echo "Node.js: $(node --version 2>/dev/null || echo 'Not found')"
    echo "npm: $(npm --version 2>/dev/null || echo 'Not found')"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "pip: $(pip3 --version 2>/dev/null || echo 'Not found')"
    echo "Docker: $(docker --version 2>/dev/null || echo 'Not found')"
    echo "AWS CLI: $(aws --version 2>/dev/null || echo 'Not found')"
    echo "Terraform: $(terraform version 2>/dev/null | head -n1 || echo 'Not found')"
}

# Run main function
main "$@"
