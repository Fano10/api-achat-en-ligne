
import json


from MVC.model import *

import pytest

def test_InsertProduct():
    produit = Produit.create(
        id = 1,
        name = "name",
        in_stock = True,
        description = "description",
        price = 5000,
        weight = 12,
        image = "image")
    
    assert produit.name == "name"
    assert produit.price ==5000
    Produit.get_by_id(1)
    Produit.delete().execute()

def test_InsertCommande():
    command = Commande.create(
        idProduit =1,
        quantity = 5,
        shipping_price = 20,
        total_price =30,
        paid = False
    )
    assert command.quantity ==5
    assert command.paid == False
    Commande.get_by_id(1)
    Commande.delete().execute()

def test_InsertClient():
    client = Client.create(
        email = "email",
        country = "country",
        adress = "address",
        postal_code = "postal_code",
        city = "city",
        province = "province"
    )
    assert client.email =="email"
    assert client.province == "province"
    Client.get_by_id(1)
    Client.delete().execute()


def test_InsertCarteCredit():
    credit = CreditCard.create(
        name = "name",
        first_digits = 0000,
        last_digits = 4444,
        expiration_year = 2024,
        expiration_month = 8
    )
    assert credit.expiration_year ==2024
    assert credit.expiration_month ==8
    CreditCard.get_by_id(1)
    CreditCard.delete().execute()

def test_InsertTransaction():
    transaction = Transaction.create(
    id = "id",
    succes = "success",
    amount_change = "amount_charged"
    )
    Transaction.get_by_id("id")
    Transaction.delete().execute()



#main du test

#db = SqliteDatabase(get_db_path())

#db.connect()

#db.close()
