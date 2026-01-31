#!/bin/bash
set -e

# ============================================================================
# ToothFairyAI MCP Server - ECS Fargate Deployment Script
# ============================================================================
#
# Usage:
#   ./deploy.sh [command]
#
# Commands:
#   setup     - Create ECR repository and initial infrastructure
#   build     - Build and push Docker image to ECR
#   deploy    - Deploy/update the ECS service
#   status    - Check service status
#   logs      - View recent logs
#   destroy   - Tear down all resources
#
# Required environment variables:
#   AWS_REGION          - AWS region (default: eu-west-1)
#   AWS_ACCOUNT_ID      - Your AWS account ID
#   VPC_ID              - VPC ID to deploy into
#   SUBNET_IDS          - Comma-separated list of subnet IDs
#
# ============================================================================

# Configuration
SERVICE_NAME="tf-mcp-server-dev"
AWS_REGION="${AWS_REGION:-ap-southeast-2}"
ECR_REPO_NAME="tf-mcp-server"
ECS_CLUSTER="tf-dev-cluster"
CONTAINER_NAME="tf-mcp-server-dev-container"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check required tools
check_prerequisites() {
    log_info "Checking prerequisites..."
    command -v aws >/dev/null 2>&1 || { log_error "AWS CLI is required but not installed."; exit 1; }
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }

    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        log_info "Detected AWS Account ID: $AWS_ACCOUNT_ID"
    fi
}

# Setup ECR repository
setup_ecr() {
    log_info "Creating ECR repository..."
    aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" 2>/dev/null || \
    aws ecr create-repository \
        --repository-name "$ECR_REPO_NAME" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true
    log_info "ECR repository ready: $ECR_REPO_NAME"
}

# Build and push Docker image
build_and_push() {
    log_info "Building Docker image..."

    # Navigate to repo root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

    cd "$REPO_ROOT"

    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

    # Login to ECR
    log_info "Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Build image
    log_info "Building image..."
    docker build -t "$SERVICE_NAME" -f tf_mcp_server/Dockerfile .

    # Tag and push
    log_info "Pushing to ECR..."
    docker tag "$SERVICE_NAME:latest" "$ECR_URI:latest"
    docker push "$ECR_URI:latest"

    log_info "Image pushed: $ECR_URI:latest"
    echo "$ECR_URI:latest"
}

# Deploy using CloudFormation
deploy_stack() {
    log_info "Deploying CloudFormation stack..."

    if [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ]; then
        log_error "VPC_ID and SUBNET_IDS environment variables are required"
        log_info "Example: VPC_ID=vpc-xxx SUBNET_IDS=subnet-xxx,subnet-yyy ./deploy.sh deploy"
        exit 1
    fi

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"

    aws cloudformation deploy \
        --template-file "$SCRIPT_DIR/cloudformation.yaml" \
        --stack-name "$SERVICE_NAME" \
        --parameter-overrides \
            ServiceName="$SERVICE_NAME" \
            ClusterName="$ECS_CLUSTER" \
            ImageUri="$ECR_URI" \
            VpcId="$VPC_ID" \
            SubnetIds="$SUBNET_IDS" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION"

    log_info "Stack deployed successfully!"

    # Get service info
    get_status
}

# Get service status
get_status() {
    log_info "Getting service status..."

    # Get task ARN
    TASK_ARN=$(aws ecs list-tasks \
        --cluster "$ECS_CLUSTER" \
        --service-name "${SERVICE_NAME}-service" \
        --region "$AWS_REGION" \
        --query 'taskArns[0]' \
        --output text 2>/dev/null)

    if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
        # Get task details
        TASK_DETAILS=$(aws ecs describe-tasks \
            --cluster "$ECS_CLUSTER" \
            --tasks "$TASK_ARN" \
            --region "$AWS_REGION" \
            --query 'tasks[0]' \
            --output json)

        STATUS=$(echo "$TASK_DETAILS" | jq -r '.lastStatus')

        # Get public IP if running
        if [ "$STATUS" == "RUNNING" ]; then
            ENI_ID=$(echo "$TASK_DETAILS" | jq -r '.attachments[0].details[] | select(.name=="networkInterfaceId") | .value')
            PUBLIC_IP=$(aws ec2 describe-network-interfaces \
                --network-interface-ids "$ENI_ID" \
                --region "$AWS_REGION" \
                --query 'NetworkInterfaces[0].Association.PublicIp' \
                --output text 2>/dev/null)

            echo ""
            log_info "Service Status: $STATUS"
            log_info "Public IP: $PUBLIC_IP"
            echo ""
            echo "MCP Endpoint: http://$PUBLIC_IP:8000/mcp/v1"
            echo "Health Check: http://$PUBLIC_IP:8000/health"
            echo "Server Info:  http://$PUBLIC_IP:8000/info"
            echo ""
        else
            log_warn "Service Status: $STATUS"
        fi
    else
        log_warn "No running tasks found"
    fi
}

# View logs
view_logs() {
    log_info "Fetching recent logs..."
    aws logs tail "/ecs/${SERVICE_NAME}-service" \
        --region "$AWS_REGION" \
        --since 30m \
        --follow
}

# Destroy all resources
destroy() {
    log_warn "This will delete all resources. Are you sure? (y/N)"
    read -r confirm
    if [ "$confirm" != "y" ]; then
        log_info "Aborted"
        exit 0
    fi

    log_info "Deleting CloudFormation stack..."
    aws cloudformation delete-stack \
        --stack-name "$SERVICE_NAME" \
        --region "$AWS_REGION"

    log_info "Waiting for stack deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$SERVICE_NAME" \
        --region "$AWS_REGION"

    log_info "Deleting ECR repository..."
    aws ecr delete-repository \
        --repository-name "$ECR_REPO_NAME" \
        --region "$AWS_REGION" \
        --force 2>/dev/null || true

    log_info "All resources deleted"
}

# Main
main() {
    check_prerequisites

    case "${1:-help}" in
        setup)
            setup_ecr
            ;;
        build)
            build_and_push
            ;;
        deploy)
            deploy_stack
            ;;
        status)
            get_status
            ;;
        logs)
            view_logs
            ;;
        destroy)
            destroy
            ;;
        all)
            setup_ecr
            build_and_push
            deploy_stack
            ;;
        *)
            echo "ToothFairyAI MCP Server - ECS Deployment"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  setup    - Create ECR repository"
            echo "  build    - Build and push Docker image"
            echo "  deploy   - Deploy CloudFormation stack"
            echo "  status   - Check service status and get endpoint"
            echo "  logs     - View recent logs"
            echo "  destroy  - Delete all resources"
            echo "  all      - Run setup, build, and deploy"
            echo ""
            echo "Required environment variables:"
            echo "  AWS_REGION     - AWS region (default: eu-west-1)"
            echo "  VPC_ID         - VPC ID to deploy into"
            echo "  SUBNET_IDS     - Comma-separated subnet IDs"
            echo ""
            echo "Example:"
            echo "  AWS_REGION=eu-west-1 VPC_ID=vpc-xxx SUBNET_IDS=subnet-a,subnet-b ./deploy.sh all"
            ;;
    esac
}

main "$@"
