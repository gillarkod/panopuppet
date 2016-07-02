# PanoPuppet & Docker

Run PanoPuppet (non SSL configuration) in a preconfigured Docker container.


## Files needed
Make sure the following files are in the current directory where you build your Docker image in.
- Dockerfile - to build the docker image
- config.yaml - PanoPuppet config file
- panopuppet.conf - Apache config file for PanoPuppet


## Building the PanoPuppet Docker image
Docker version < 1.9.0  
If a proxy is needed, you will need to edit the Dockerfile.  
```
# vim Dockerfile
<set following environment settings>
ENV http_proxy http://proxy.company.co.uk:8080
ENV https_proxy https://proxy.company.co.uk:8080

# docker build -t panopuppet:v1.4.0  .
```

Docker version >= 1.9.0  
--build-args can be specified for a proxy, if needed.
```
# docker build -t panopuppet:v1.4.0 --build-arg http_proxy=http://proxy.company.co.uk:8080 --build-arg https_proxy=https://proxy.company.co.uk:8080 .
```

Display the Docker images
```
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
panopuppet          v1.4.0              df6e3453cd37        57 minutes ago      530.4 MB
docker.io/centos    6                   6a77ab6655b9        4 weeks ago         194.6 MB
docker.io/centos    7                   904d6c400333        4 weeks ago         196.7 MB
```


### Starting the PanoPuppet container
```
# docker run --restart=always -dt --name=panopuppet -p 90:80 panopuppet:v1.4.0
```

What this says is;
- create a running container
- -give it name panopuppet
- set it to always restart, which means when the docker service starts this container will start. 
- -p means publish a containers port; in this case the systems port 90 will be mapped to the containers port 80; replace 90 with whatever you want/is free on your host.


### Checking status PanoPuppet container
```
# docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                NAMES
d327335e55c9        panopuppet:v1.4.0   "apachectl -D FOREGRO"   3 seconds ago       Up 1 seconds        0.0.0.0:90->80/tcp   panopuppet
```


### Adding a superuser
```
# docker exec -it d327335e55c9 bash
  cd /var/www/panopuppet
  python3.5 mange.py createsuperuser
```

