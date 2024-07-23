import os
import traceback
import click
from flask.cli import with_appcontext  #importation des modules necessaires pour la creation du modele
import pg8000
import psycopg2
import redis
from peewee import *

def get_db_postgreSQL(): # cette fonction retourne une reference connecte a notre base de donnee postgreSQL
    vDatabase = os.environ.get('DB_NAME')
    vUser = os.environ.get('DB_USER')
    vDB_HOST = os.environ.get('DB_HOST')
    vPassword = os.environ.get('DB_PASSWORD')
    vPort = os.environ.get('DB_PORT')

    db = PostgresqlDatabase(database=vDatabase,user=vUser,password=vPassword,host=vDB_HOST,port=vPort)
    return db

def get_db_redis(): # cette fonction retourne une reference connecte a notre base de donne redis
    vRedisUrl = os.environ.get('REDIS_URL')
    dbRedis = redis.Redis.from_url(vRedisUrl)
    return dbRedis


class BaseModel(Model): #une classe de base pour tous les modèles de données de l'application.
    class Meta:
        #database = SqliteDatabase(get_db_path())
        database = get_db_postgreSQL()

class Produit(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    in_stock = BooleanField()
    description = CharField()
    price = FloatField()
    weight = IntegerField()
    image = CharField()

    
class Client(BaseModel):
    id = AutoField(primary_key=True)
    email = CharField(null=False)
    country = CharField(null=False)
    adress = CharField(null=False)
    postal_code = CharField(null=False)
    city = CharField(null=False)
    province = CharField(null=False)
    

class CreditCard(BaseModel):
    id = AutoField(primary_key=True)
    name = CharField(null=False)
    first_digits = CharField(null=False)
    last_digits = CharField(null=False)
    expiration_year = IntegerField(null =False)
    expiration_month = IntegerField(null =False)

class Transaction(BaseModel):
    id = AutoField(primary_key = True)
    idSucces = CharField(null = True)
    succes = BooleanField(null =True)
    code = CharField(null=True)
    name = CharField(null=True)
    amount_change = IntegerField(null =True)

class Commande(BaseModel):
    id = AutoField(primary_key=True)
    idClient = IntegerField(null =True)
    idCreditCard = IntegerField(null =True)
    idTransaction = IntegerField(null =True)
    paid = BooleanField(null =True)
    shipping_price = IntegerField(null =True)
    total_price = IntegerField(null =True)

class Panier(BaseModel):
    idCommande = IntegerField(null=True)
    idProduit = IntegerField(null=True)
    quantity = IntegerField(null=True)



@click.command("init-db")
@with_appcontext
def init_db_command(): #initialisation de la base de donnee
    mesModeles = [Produit,Client,CreditCard,Transaction,Commande,Panier]
    database = get_db_postgreSQL()
    redis = get_db_redis()
    try:
        redis.flushall() # assurer de vider la cache
        database.drop_tables(mesModeles)
    except Exception as e :
        click.echo("Aucune table dans le db: ",e)
    try:
        database.create_tables(mesModeles)
        click.echo("Initialized the database.")
    except Exception as e:
        click.echo("Error initializing the database")
def init_app(app):
    app.cli.add_command(init_db_command)