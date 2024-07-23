from flask import make_response,jsonify
from MVC.model import Produit,Client,Transaction,CreditCard,Commande,Panier


class ViewAllProducts(object): #OK
    allProduct = Produit

    def __init__(self,allProduit):#allProduit ici c'est un liste d'objet de produit
        self.allProduct = allProduit
    
    def response(self):
        tab_dict = []
        for produit in self.allProduct:
            dict_produit = {"id":produit.id,"name":produit.name,"in_stock":produit.in_stock,"description":produit.description,"price":produit.price,"weight":produit.weight,"image":produit.image}
            tab_dict.append(dict_produit)

        data = {"products": tab_dict}

        # Créer un objet de réponse avec JSON, code de statut et en-têtes
        response = make_response(jsonify(data))
        response.status_code = 200  # 200 correspond à OK
        response.headers['Content-Type'] = 'application/json'
        return response
    

class ViewCommande(object):
    commande = Commande
    client = Client
    transaction = Transaction
    cardCredit = CreditCard
    panier = Panier

    def __init__(self,commande,client,transaction,cardCredit):
        self.commande = commande
        self.client = client
        self.transaction = transaction
        self.cardCredit = cardCredit

    def response(self):
        if(self.client is not None):
            shipping_information = {"country":self.client.country,
                                    "address":self.client.adress,
                                    "postal_code":self.client.postal_code, #vue pour le client
                                    "city": self.client.city,
                                    "province":self.client.province}
            email = self.client.email
        else:
            shipping_information = {}
            email = None
        if(self.cardCredit is not None):
            credit_card = {"name": self.cardCredit.name,
                           "first_digits":self.cardCredit.first_digits,
                           "last_digits":self.cardCredit.last_digits,
                           "expiration_year":self.cardCredit.expiration_year,
                           "expiration_month":self.cardCredit.expiration_month}
        else:
            credit_card = {}
        if(self.transaction is not None):
            if(self.transaction.name is not None):
                error = {"name": self.transaction.name,
                         "code":self.transaction.code}
            else:
                error = {}
            transaction = {"id":self.transaction.idSucces,
                           "success":self.transaction.succes,
                           "amount_charger":self.transaction.amount_change,
                           "error":error}
        else:
            transaction = {}

        dataPanier = []
        paniers = Panier.select().where(Panier.idCommande==self.commande.id)
        for panier in paniers:
            intermediaire = {"id":panier.idProduit,"quantity":panier.quantity}
            dataPanier.append(intermediaire)

        if(len(dataPanier) ==1):
            cleProduit = "product"
            dataPanier = dataPanier[0]
        else:
            cleProduit = "products"
        data = {"id":self.commande.id,
                "shipping_price":self.commande.shipping_price,
                "total_price":self.commande.total_price,
                "paid":self.commande.paid,
                "email":email,
                cleProduit:dataPanier,
                "shipping_information":shipping_information,
                "credit_card":credit_card,
                "transaction":transaction}
    
        data = {"order": data}
         # Créer un objet de réponse avec JSON, code de statut et en-têtes
        response = make_response(jsonify(data))
        response.status_code = 200  # 200 correspond à OK
        response.headers['Content-Type'] = 'application/json'
        return response
    
class ViewCacheCommand(object): # cette classe est destine pour retourner a partir de la cache

    def __init__(self,command):
        self.command = command
    def response(self):
        response = make_response(self.command)
        response.status_code = 200  # 200 correspond à OK
        response.headers['Content-Type'] = 'application/json'
        return response
    
class ViewError(object): # cette classe est destine pour les retours des erreurs
        
    def __init__(self,categorie,codeStatut,codeDescription,name):
        self.categorie = categorie
        self.codeStatut =codeStatut
        self.codeDescription = codeDescription
        self.name = name
            
    def response(self):
        data = {"errors":{self.categorie:{"code":self.codeDescription,"name":self.name}}}
        #data = {"errors":"erreur"}
        response = make_response(jsonify(data))
        response.status_code = self.codeStatut
        response.headers['Content-Type'] = 'application/json'
        return response