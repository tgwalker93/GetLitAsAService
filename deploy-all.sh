#!/bin/sh
kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

kubectl apply -f rest/rest-deployment.yaml
kubectl apply -f rest/rest-service.yaml

kubectl apply -f logs/logs-deployment.yaml

kubectl apply -f worker/worker-deployment.yaml

kubectl apply -f minio/minio-external-service.yaml

kubectl apply -f rest/rest-ingress.yaml

#For SSH into a specific pod
#kubectl exec -it pod/worker-deployment-668d7d559-dvvs2 -- bash