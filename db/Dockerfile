FROM postgres:14-alpine

RUN mkdir -p /var/log/postgresql/ && chmod -R 0777 /var/log/postgresql/
COPY init.sql /docker-entrypoint-initdb.d/