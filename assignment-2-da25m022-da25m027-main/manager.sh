#! /bin/bash

docker stack deploy -c stack.yaml assign2
docker swarm init --advertise-addr 127.0.0.1
docker stack ps assign2

# docker service update assign2_api_service
# docker service ps assign2_api_service

# docker stack rm hello

# docker node update --label-add node_ID
# docker swarm leave

