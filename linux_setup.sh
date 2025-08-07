#!/bin/bash

# Function to print colored output
print_status() {
    echo -e "\e[1;34m>>> $1\e[0m"
}

print_success() {
    echo -e "\e[1;32m✓ $1\e[0m"
}

print_error() {
    echo -e "\e[1;31m✗ $1\e[0m"
}

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Get the actual username (not root)
ACTUAL_USER=$SUDO_USER
if [ -z "$ACTUAL_USER" ]; then
    print_error "Could not determine the actual user"
    exit 1
fi

print_status "Starting setup for PyCon 2025 Benchmarking..."

# Install Docker
print_status "Installing Docker..."
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
print_success "Docker installed successfully"

# Add user to docker group
print_status "Adding user to docker group..."
usermod -aG docker $ACTUAL_USER
print_success "User added to docker group"

# Install development packages
print_status "Installing development packages..."
apt-get update
apt-get install -y libpq-dev python3-dev build-essential
print_success "Development packages installed"

# Install UV package manager
print_status "Installing UV package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
print_success "UV package manager installed"

# Run uv sync as the actual user
print_status "Running uv sync..."
# Switch to the actual user and run uv sync in the current directory
su - $ACTUAL_USER -c "cd $(pwd) && uv sync"
print_success "UV sync completed"

# Final setup
print_status "Finalizing setup..."
newgrp docker

# Build all docker images
print_status "Building Docker images..."
docker compose -f docker-compose.benchmark.yml build
print_success "Docker images built successfully"

print_success "Setup completed successfully!"
print_status "Please log out and log back in for group changes to take effect"
print_status "Then you can run: docker ps to verify docker access"