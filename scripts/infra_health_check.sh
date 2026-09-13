#!/bin/bash

LOG_FILE="/var/log/infra_health.log"
APP_CONTAINER="devops_trainee_assignment-backend-1"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_warning() {
    local message="$1"
    echo "$(timestamp) [WARNING] $message" | sudo tee -a "$LOG_FILE" > /dev/null
}

echo "========================================"
echo "Infrastructure Health Check"
echo "Timestamp: $(timestamp)"
echo "========================================"

# CPU usage
CPU_USAGE=$(top -bn1 | awk '/Cpu\(s\)/ {print 100 - $8}')
printf "CPU Usage: %.1f%%\n" "$CPU_USAGE"

# RAM usage
RAM_USAGE=$(free | awk '/Mem:/ {printf "%.1f", $3/$2 * 100}')
printf "RAM Usage: %.1f%%\n" "$RAM_USAGE"

# Root disk usage
DISK_USAGE=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')
echo "Root Disk Usage: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 85 ]; then
    echo "[WARNING] Root disk usage exceeds 85%."
    log_warning "Root disk usage is ${DISK_USAGE}%"
fi

# Docker service status
if systemctl is-active --quiet docker; then
    echo "Docker Status: running"
else
    echo "[WARNING] Docker service is not running."
    log_warning "Docker service is not running"
fi

# Application container status
if docker inspect -f '{{.State.Status}}' "$APP_CONTAINER" 2>/dev/null | grep -q '^running$'; then
    echo "Application Container: running"
else
    echo "[WARNING] Application container is stopped or unavailable."
    log_warning "Application container '$APP_CONTAINER' is stopped or unavailable"
fi

echo "========================================"
