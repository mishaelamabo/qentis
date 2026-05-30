#!/bin/bash
set -e

DOCKER_USER="nebamishael"

echo ">>> Logging in to Docker Hub..."
docker login -u $DOCKER_USER

echo ">>> Building images..."
cd ../services

docker build -t $DOCKER_USER/qentis-user-auth:latest        ./user-auth
docker build -t $DOCKER_USER/qentis-institution:latest      ./institution
docker build -t $DOCKER_USER/qentis-item-registration:latest ./item-registration
docker build -t $DOCKER_USER/qentis-blockchain:latest       ./blockchain
docker build -t $DOCKER_USER/qentis-auth-output:latest      ./auth-output
docker build -t $DOCKER_USER/qentis-verification:latest     ./verification
docker build -t $DOCKER_USER/qentis-admin-analytics:latest  ./admin-analytics

echo ">>> Pushing images to Docker Hub..."
docker push $DOCKER_USER/qentis-user-auth:latest
docker push $DOCKER_USER/qentis-institution:latest
docker push $DOCKER_USER/qentis-item-registration:latest
docker push $DOCKER_USER/qentis-blockchain:latest
docker push $DOCKER_USER/qentis-auth-output:latest
docker push $DOCKER_USER/qentis-verification:latest
docker push $DOCKER_USER/qentis-admin-analytics:latest

echo "✅ All images pushed to hub.docker.com/u/nebamishael"
docker logout