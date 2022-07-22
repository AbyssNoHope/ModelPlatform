#!/bin/bash

for HOST in gpu1.cluster.peidan.me; do
(
  IP="$(python3 -c "import socket; print(socket.gethostbyname('${HOST}'))")"
  ssh-keygen -f "/root/.ssh/known_hosts" -R "${HOST}"
  ssh-keygen -f "/root/.ssh/known_hosts" -R "${IP}"
);
done
