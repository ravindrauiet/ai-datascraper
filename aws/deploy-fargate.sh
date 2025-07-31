#!/bin/bash

# Pinterest Scraper AWS Fargate Deployment Script
# This script handles the complete deployment process including environment variable substitution

set -e

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPOSITORY=pinterest-scraper-api
ECS_CLUSTER=${ENVIRONMENT}-pinterest-cluster
ECS_SERVICE=${ENVIRONMENT}-pinterest-scraper-api

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Pinterest Scraper deployment to AWS Fargate...${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}AWS Region: ${AWS_REGION}${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}Creating ECR repository if it doesn't exist...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} > /dev/null 2>&1 || \
aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}

# Login to ECR
echo -e "${YELLOW}Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY}:latest .

echo -e "${YELLOW}Tagging Docker image...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

echo -e "${YELLOW}Pushing Docker image to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Substitute variables in task definition
echo -e "${YELLOW}Preparing ECS task definition...${NC}"
cp aws/task-definition.json aws/task-definition-${ENVIRONMENT}.json

# Replace placeholders with actual values
sed -i.bak "s/\${AWS_ACCOUNT_ID}/${AWS_ACCOUNT_ID}/g" aws/task-definition-${ENVIRONMENT}.json
sed -i.bak "s/\${AWS_REGION}/${AWS_REGION}/g" aws/task-definition-${ENVIRONMENT}.json
rm aws/task-definition-${ENVIRONMENT}.json.bak

# Register task definition
echo -e "${YELLOW}Registering ECS task definition...${NC}"
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://aws/task-definition-${ENVIRONMENT}.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo -e "${GREEN}Task definition registered: ${TASK_DEFINITION_ARN}${NC}"

# Check if ECS service exists
echo -e "${YELLOW}Checking if ECS service exists...${NC}"
if aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --query 'services[0].serviceName' --output text 2>/dev/null | grep -q ${ECS_SERVICE}; then
    echo -e "${GREEN}Service exists. Updating service...${NC}"
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --task-definition ${TASK_DEFINITION_ARN} \
        --force-new-deployment
else
    echo -e "${YELLOW}Service doesn't exist. Creating new service...${NC}"
    # Note: This assumes the CloudFormation stack has been deployed first
    # to create the necessary infrastructure (VPC, subnets, security groups, etc.)
    echo -e "${RED}Warning: ECS service not found. Please deploy the CloudFormation stack first.${NC}"
    echo -e "${YELLOW}You can create the service manually or through CloudFormation.${NC}"
fi

# Wait for deployment to complete
echo -e "${YELLOW}Waiting for deployment to stabilize...${NC}"
aws ecs wait services-stable --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE}

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Get service information
SERVICE_INFO=$(aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --query 'services[0]')
RUNNING_COUNT=$(echo ${SERVICE_INFO} | jq -r '.runningCount')
DESIRED_COUNT=$(echo ${SERVICE_INFO} | jq -r '.desiredCount')

echo -e "${GREEN}Service Status:${NC}"
echo -e "  Running tasks: ${RUNNING_COUNT}"
echo -e "  Desired tasks: ${DESIRED_COUNT}"

# Get load balancer DNS name if available
if aws elbv2 describe-load-balancers --names ${ENVIRONMENT}-pinterest-alb > /dev/null 2>&1; then
    ALB_DNS=$(aws elbv2 describe-load-balancers --names ${ENVIRONMENT}-pinterest-alb --query 'LoadBalancers[0].DNSName' --output text)
    echo -e "${GREEN}Application URL: http://${ALB_DNS}${NC}"
fi

echo -e "${GREEN}Deployment script completed!${NC}"
