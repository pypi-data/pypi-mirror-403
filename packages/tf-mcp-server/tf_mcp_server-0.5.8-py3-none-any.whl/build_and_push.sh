#!/usr/bin/env bash

image=$1
# AWS_ACCESS_KEY_ID=$2
# AWS_SECRET_ACCESS_KEY=$3

ACCOUNT_ID=$(aws sts get-caller-identity --query Account | tr -d '"')
# default aws_region to ap-southeast-2
AWS_REGION=${2:-'ap-southeast-2'}
TAG='latest'

fullname="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${image}:${TAG}"

# If the repository doesn't exist in ECR, create it.
output=$(aws ecr describe-repositories --repository-names ${image} 2>&1)

if [ $? -ne 0 ]; then
  if echo ${output} | grep -q RepositoryNotFoundException; then
    aws ecr create-repository --repository-name ${image}
  else
    >&2 echo ${output}
  fi
fi

# Get the login command from ECR and execute it directly
$(aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com)

# # Copy files from folder 
# mkdir -p ./tmp/Common
# cp -r ../Common ./tmp/Common
# # Create directory

# Build the docker image locally and then push it to ECR with the full name.

echo "Building image with name ${image}"
docker build -t ${image} -f Dockerfile .
docker tag ${image} ${fullname}

echo "Pushing image to ECR ${fullname}"
docker push ${fullname}
