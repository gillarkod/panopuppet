# Introduction

I wanted to run panopuppet v0.x on a centos 6 puppetmaster (puppet 3.6.2; puppetdb 2.1).
The puppet master uses apache and mod-wsgi for python 2.6 (Phusion Passenger, etc).
Panopuppet uses python 3.3, and mod-wsgi for two different python releases does not co-exist easily in one apache. I could use nginx, but I would then need to work out the mod-wsgi for that, and I am not sure it would work/is supported. Thus I thought I would try and containerize it using docker.

Docker image size is 489Mb. When the container is running it only consumes 60Mb of memory; that is so much better than a vm!

For later versions of the puppet master, a dedicate puppetmaster process is used (java based) rather than apache. On puppet 4.5 (puppetserver 2.4.0/puppetdb 4.1) there is no need for apache, although you may wish to have panopuppet and puppetboard together, so you may wish to containerize one of them because of the wsgi issue. There is also wsgi express that allows different python wsgi's to coexist; another thing you could spend time on learning and trying to use!

## Files needed
You can take this from the git panopuppet v0.x release (git clone...). Make sure these are in the current dir that you build your docker image in.
- Dockerfile - To build the docker image
- panopuppet.conf - apache conf file for panopuppet; see install notes.
- config.yaml - ready configured config.yaml

## Install docker

I tested this with docker-io 1.7.1 from epel on centos 6 (same release as the puppet master). Its probably important to get your centos 6 system up to date (I used 6.8). Start docker and make sure its in the startup:

```
# service docker start
# chkconfig docker on
```
## Building the docker image
You will find some ENV proxy settings in the docker file; set these if you are behind a firewall and need proxy access. I also needed to export these in /etc/sysconfig/docker (and restart docker to take effect).

Building the docker image; this will take a while; be patient:

```
# docker build -t panopuppet:v0.x  .
```
You can then check this:

```
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
panopuppet          v0.x                5382ecea9d40        57 minutes ago      489.1 MB
centos              6                   a0f8f0620fa4        3 weeks ago         194.6 MB
```

### Creating a container and starting it
We either use docker run or docker create; they do pretty much the same thing. Lets do docker run as it will also start it up for us:

```
# docker run --restart=always -dt --name=panopuppet -p 90:80 panopuppet:v0.x
```

What this says is create a running container, give it name panopuppet, set it to always restart, which means when the docker service starts this container will start. The -p means publish a containers port; in this case the systems port 90 will be mapped to the containers port 80; replace 90 with whatever you want/is free on your host

We can check its status:

```
# docker ps -a
CONTAINER ID        IMAGE               COMMAND                CREATED             STATUS              PORTS             NAMES
44787320db82        panopuppet:v0.x     "/bin/sh -c 'service   About an hour ago   Up 48 minutes       0.0.0.0:90->80/tcp   panopuppet
```

Note that the difference between the image and container is that the container has a writeable filesystem which maintains state. If you wipe the container (docker rm) and recreate it, it will wipe any new files written into the container. Eg any tweaks you made to config.yaml or any pano search filters you created and saved!

### Connect to the container while its running
We might want to go in and change the config.yaml, or look at the apache logs. This is how I do it:

```
# docker exec -it 44787320db82 bash
```
You can ctrl d out of that or ctrl p then ctrl q. If you do a docker ps -a again you will see its still running.

### Adding a superuser
Connect to the container as described above. Then this is a cut and paste from the install instructions:

```
# workon panopuppet
# cd /srv/repo/panopuppet
# python mange.py createsuperuser
```

### Test auto restart of the container
Its as simple as restarting the docker service and checking the container has been started:

```
# service docker restart
# docker ps -a
CONTAINER ID        IMAGE               COMMAND                CREATED             STATUS              PORTS                NAMES
44787320db82        panopuppet:v0.x     "/bin/sh -c 'service   About an hour ago   Up 4 seconds        0.0.0.0:90->80/tcp   panopuppet
```

### Apache redirect to the container
I did it this way. We have puppet board at http://puppet, so I would like pano at http://puppet/pano. So I created this apache conf file on the host to redirect a link to port 90:

```
# cat /etc/httpd/conf.d/panopuppet.conf
Redirect 302 /pano http://puppet:90
```



