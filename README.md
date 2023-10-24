# Api for LLM setup guide

[Initial server setup guide](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04)

`sudo apt update`

`sudo apt upgrade`

`sudo reboot`

## Docker setup

[DO guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04#step-1-installing-docker)

[Compose install](https://docs.docker.com/compose/install/linux/)

*Everything above can be skipped using the cloud init script*

To check the cloud-init logs:

`sudo cat /var/log/cloud-init-output.log`

`sudo cat /var/log/cloud-init.log`

## Setup project

`git clone https://github.com/don-dp/apiforllmdjango.git`

Set environment variables in `~/.bashrc`

`APIFORLLMDJANGO_SECRET_KEY`: The secret key for your Django application.

`APIFORLLMDJANGO_DEBUG`: Set this to True for debugging. Use False in production.

`APIFORLLMDJANGO_ALLOWED_HOSTS`: A comma-separated list of hosts/domains your app can serve.

`APIFORLLMDJANGO_DEFAULT_FROM_EMAIL`: Default 'from' email address for sending mails.

`APIFORLLMDJANGO_EMAIL_BACKEND`: Backend to use for sending emails.

`APIFORLLMDJANGO_EMAIL_HOST`: SMTP service host.

`APIFORLLMDJANGO_EMAIL_PORT`: Port number for the email service.

`APIFORLLMDJANGO_EMAIL_USE_TLS`: Use TLS for email, typically True or False.

`APIFORLLMDJANGO_EMAIL_HOST_USER`: Username for the email service.

`APIFORLLMDJANGO_EMAIL_HOST_PASSWORD`: Password for the email service.

`APIFORLLMDJANGO_TURNSTILE_SECRET_KEY`: Secret key for Turnstile.

`APIFORLLMDJANGO_POSTGRES_USER`: PostgreSQL database user.

`APIFORLLMDJANGO_POSTGRES_PASSWORD`: PostgreSQL database password.

`APIFORLLMDJANGO_POSTGRES_DB`: Name of the PostgreSQL database.

`APIFORLLMDJANGO_NGINX_CONFIG`: nginx.prod.conf or nginx.dev.conf

`APIFORLLMDJANGO_ENV`: Sets the environment. Could be local or prod.

`APIFORLLMDJANGO_OPENAI_KEY`: API key for OpenAI.

`source ~/.bashrc`

`mkdir /home/sammy/certs`

`sftp user@ip`

`put -r /home/dp/Desktop/certs/apiforllmdjango/* /home/sammy/certs/`

Enable full strict ssl and authenticated pulls

`cd apiforllmdjango`

`docker compose up -d`

`sudo ufw allow 80`

`sudo ufw allow 443`

## Backup and restore database

`docker exec -t <container_id> pg_dump -U $APIFORLLMDJANGO_POSTGRES_USER -d $APIFORLLMDJANGO_POSTGRES_DB > backup.sql`

`docker exec -it <container_id> psql -U <username> -d postgres -c "drop database <db_name>;"`

`docker exec -it <container_id> psql -U $APIFORLLMDJANGO_POSTGRES_USER -l`

`docker exec -it <container_id> psql -U $APIFORLLMDJANGO_POSTGRES_USER -d postgres -c "create database $APIFORLLMDJANGO_POSTGRES_DB;"`

`docker exec -i <container_id> psql -U $APIFORLLMDJANGO_POSTGRES_USER -d $APIFORLLMDJANGO_POSTGRES_DB < backup.sql`