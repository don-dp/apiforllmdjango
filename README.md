# Api for LLM setup guide

[Initial server setup guide](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04)

`sudo apt update`

`sudo apt upgrade`

`sudo reboot`

## Docker setup

[DO guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04#step-1-installing-docker)

[Compose install](https://docs.docker.com/compose/install/linux/)

*Everything above can be skipped using the cloud init script*

[Create a deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#deploy-keys) if required.

## Setup project

`git clone git@github.com:don-dp/apiforllmdjango.git`

Set environment variables in `~/.bashrc`

`source ~/.bashrc`

`mkdir /home/sammy/certs`

`sftp user@ip`

`put -r /home/dp/Desktop/certs/apiforllmdjango/* /home/sammy/certs/`

Enable full strict ssl and authenticated pulls

`cd apiforllmdjango`

`docker compose up -d`

`sudo ufw allow 80`

`sudo ufw allow 443`

## Export database

`docker exec -t <container_id> pg_dump -U $APIFORLLMDJANGO_POSTGRES_USER -d $APIFORLLMDJANGO_POSTGRES_DB > backup.sql
`