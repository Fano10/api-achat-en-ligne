FROM python:3.7-buster

RUN pip install --upgrade pip
RUN pip install flask pytest peewee pg8000 redis psycopg2 rq
EXPOSE 5000
#copier le fichier CODE-PERMANENT RAKM11100201 et changer son nom en site
COPY code /site
# Définition de l'argument ARG
ARG FLASK_APP
ARG FLASK_DEBUG
ARG REDIS_URL
ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD
ARG DB_PORT
ARG DB_NAME
# Définition de la variable d'environnement ENV
ENV FLASK_APP=$FLASK_APP
ENV FLASK_DEBUG=$FLASK_DEBUG
ENV REDIS_URL=$REDIS_URL
ENV DB_HOST=$DB_HOST
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_PORT=$DB_PORT
ENV DB_NAME=$DB_NAME
#Nous avons utilisé WORKDIR /site pour définir le répertoire de travail de l'image Docker sur /site.
WORKDIR /site
#initialisation du bd
RUN flask init-db
#commande pour demmarer notre application
CMD python /site/api8inf349.py
