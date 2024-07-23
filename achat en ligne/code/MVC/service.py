from urllib.request import urlopen,Request
from flask import redirect,url_for,make_response
from MVC.model import Produit,Commande,Client,Transaction,CreditCard,Panier,get_db_redis
from MVC.view import ViewError,ViewCommande,ViewCacheCommand
import json
import time
import traceback
from rq import Queue,Worker

global_queue = Queue # notre file que nous allons utiliser pour gerer notre work


def Initialization(): #cette fonction récupère les produits lors de la lancement de l'appliaction et l'insère dans la base de donnée
    urlProduct  = "http://dimprojetu.uqac.ca/~jgnault/shops/products/"
    data = CollectProducts(urlProduct)
    if(data is not None):#vérification s'il existe des produits
        for product in data["products"]: # insertion dans la base de donne
            try:
                InsertProduct(product)
            except Exception as e:
                pass

def CollectProducts(url): #cette fonction récupère les produits vers un url
    try:
        response = urlopen(url) # utilisation de urlopen pour ouvrir le lien
        assert response.code == 200
        assert response.headers['Content-Type'] == 'application/json'
        data = response.read()# le json retournée par le serveur
        payload = json.loads(data)
    except:
        payload = None
    return payload # retourne les données récuperer 

def InsertCheckCommand(data): #assure la vérification du donnée recu et insère a la fois la commande(retourne une erreur ou une redirection vers la methode get). Ancien version d'insertion de commande
    try:
        if(isinstance(data,list)):
            error = ViewError("order",422,"lots-of-content","un seul produit par achat est acceépté")
            return error.response()
        try:
            id = data["id"]
            quantity = data["quantity"]
            if (not(isinstance(id,int)) or not(isinstance(quantity,int))):
                error = ViewError("product",422,"type-error","La creation d\'une commande nécéssite un produit")
                return error.response()
        except:
            error = ViewError("product",422,"missing-fields","La creation d\'une commande nécéssite un produit")
            return error.response()           
    except:
        error = ViewError("order",422,"table error","Seul le type produit est accépté dans le json")
        return error.response()
    try: 
        productSelect = Produit.get_by_id(data["id"])
    except:
        error = ViewError("product",422,"missing-fields","Le produit n\'existe pas")
        return error.response()
    try:
        if(productSelect.in_stock == False):
            raise Exception("Le produit demandé n\'est pas en inventaire")
        if(data["quantity"]<1):
            raise Exception("La quantité n'est pas suffisant")
    except Exception as e:
        error = ViewError("product",422,"missing-fields",str(e))
        return error.response()
    
    #Toutes les vérifications sont bien fini, il faut maintenant insérer la nouvelle commande
    data = [data]#necessaire car la fonction NewCommand ne recoit que des tableaux
    productSelect = [productSelect]
    idNewCommand = NewCommand(productSelect,data)
    return  redirect(url_for('getCommande',order_id = idNewCommand))

def InsertCheckCommandTab(data): #assure la vérification du donnée recu et insère a la fois la commande(retourne une erreur ou une redirection vers la methode get). Nouvelle version d'insertion de commande
    if len(data) == 0:#assurer qu'il y a au moins une commande dans le product
        error = ViewError("order",422,"missing-fields","La creation d\'une commande nécéssite au moins un produit")
        return error.response()
    tabProduitSelect = []  # liste des produits a commander
    for element in data :#verifier chaque produit dans la commande, retourne directement un erreur si un produit ne correspond pas au exigence 
        try:
            id = element["id"]
            quantity = element["quantity"]
            if (not(isinstance(id,int)) or not(isinstance(quantity,int))):
                error = ViewError("product",422,"type-error","champs manquant pour un ou plusieus produits")
                return error.response()
        except:
            error = ViewError("product",422,"missing-fields","champs manquant pour un ou plusieus produits")
            return error.response()           
        try: 
            productSelect = Produit.get_by_id(element["id"])
            if(productSelect.in_stock == False):
                raise Exception("Le(s) produit(s) demandé(s) n\'est ou ne sont pas en inventaire")
            if(element["quantity"]<1):
                raise Exception("La quantité n'est pas suffisant pour un ou plusieurs produits")
            tabProduitSelect.append(productSelect) # ajout du produit dans la lise
        except Exception as e:
            error = ViewError("product",422,"missing-fields",str(e))
            return error.response()
    
    #Toutes les vérifications sont bien fini, il faut maintenant insérer la/les nouvelles commandes
    idNewCommand = NewCommand(tabProduitSelect,data)
    return  redirect(url_for('getCommande',order_id = idNewCommand))

def NewCommand(products,data): # créer toutes les champs nécéssaires pour la nouvelle commande
    totalPrice = 0
    totalWeight = 0
    shippingPrice = 0
    i = 0
    for element in data:#calcul le poids total et le prix total de chaque element
        totalPrice = totalPrice + products[i].price * element["quantity"]
        totalWeight =totalWeight + products[i].weight * element["quantity"]
        i = i + 1
    if(totalWeight <= 500):
        shippingPrice = 5
    elif(totalWeight <= 2000):
        shippingPrice = 10
    else:
        shippingPrice = 25
    dataFinal = {"total_price":totalPrice,"shipping_price":shippingPrice}
    dataInsert = InsertCommand(dataFinal)
    i = 0
    for produit in products:
        dataPanier = {"idCommande":dataInsert.id,"idProduit":produit.id,"quantity":data[i]["quantity"]}
        InsertPanier(dataPanier)
        i = i + 1
    return dataInsert.id



def GetCommand(order_id,global_queue): # cette fonction s'occupe de la récupération du commande selon l'ID
    valeur = checkCache(order_id)
    if(valeur is not None):# on verifie d'abord dans la cache
        response = ViewCacheCommand(valeur)
        return response.response()

    try: #si la commande n'est pas encore dans la cache
        commande = Commande.get_by_id(order_id)
        try:
            client = Client.get_by_id(commande.idClient)
        except:
            client = None
        try:
            cardCredit = CreditCard.get_by_id(commande.idCreditCard)
            print("cardCredit")
        except:
            cardCredit = None
            print("pas de cardCredit")
        try:
            transaction = Transaction.get_by_id(commande.idTransaction)
        except:
            transaction = None
        response = ViewCommande(commande,client,transaction,cardCredit)
        print("est ce que le print marche au moins")
        if(transaction is not None and cardCredit is not None):# si l'achat est effectuer avec succes, on insere dans la cache la commande
            data = (response.response()).data
            insertCache(data,order_id)
        return response.response()
    except Exception as e:
        codeStatut = 422
        codeDescription = "out-of-command"
        categorie = "order"
        name = "La commande n\'éxiste pas"
        erreur = ViewError(categorie,codeStatut,codeDescription,name)
        print(e)
        return erreur.response()
    
def checkCache(order_id): #cette fonction verifie d'abords dans la cache avant de proceder dans la bd
    redis = get_db_redis()
    valeur = redis.get(order_id)
    return valeur

def insertCache(data,order_id):# cette fonction insere dans redis une nouvelle commande deja paye
    redis = get_db_redis()
    try:
        redis.set(order_id,data)
    except:
        print("Probleme d'insertion dans redis")

def UpdateClient(commandSelect,data):# cette fonction vérifie et met à jour la table client
    try:
        email = data["order"]["email"]
        information = data["order"]["shipping_information"]
        newClient = InsertClient(email,information)
        commandSelect.idClient = newClient.id
        commandSelect.save()
        return  redirect(url_for('getCommande',order_id = commandSelect.id))
    except Exception as e:
        erreur = ViewError("order",422,"missing-fields","Il manque un ou plusieurs champs qui sont obligatoires")
        return erreur.response()


def PayementIntegration(selectCommand,data,amountCharged): # cette fonction s'occupe de l'intéraction avce l'API distant
        time.sleep(1)
        url  = "http://dimprojetu.uqac.ca/~jgnault/shops/pay/"
        headers = {"content-type":"application/json"}
        try:
            req = Request(url,data,headers)
            try:
                response = urlopen(req)
                headers = response.headers
                jsonData = response.read()
                httpCode = response.code
                assert headers["Content-Type"] == 'application/json' #vérifier qu'on a bien obtenu un JSON
                dictData = json.loads(jsonData)
                infCredit = dictData["credit_card"]
                infTransaction = dictData["transaction"]
                #ajout de valeur nulle pour le cle code et name/Nouvelle fonctionnalite
                infTransaction['code'] = None
                infTransaction['name']=None
                infTransaction['succes'] = infTransaction["success"]
                newCredit = InsertCreditCard(infCredit)
                selectCommand.idCreditCard = newCredit.id
                newTransaction = InsertTransaction(infTransaction)#InsertTransaction modifie
                selectCommand.paid = newTransaction.succes
                selectCommand.idTransaction = newTransaction.id
                selectCommand.save()
                print(selectCommand.paid)
                print(selectCommand.idCreditCard)
                print(selectCommand.idTransaction)
                return True
            except Exception as e: #si le serveur retourne un erreur
                httpCode = e.code
                errorData = json.loads(e.read())
                infTransaction = errorData["errors"]["credit_card"]
                infTransaction['id'] = None
                infTransaction['idSucces'] = None
                infTransaction['succes'] = False
                infTransaction['amount_charged'] = amountCharged
                #error = ViewError("credit_card",httpCode,errorData["credit_card"]["code"],errorData["credit_card"]["name"])
                #return error.response()
            #si le serveur ne retourne pas un erreur
                newTransaction = InsertTransaction(infTransaction)#InsertTransaction modifie
                selectCommand.paid = newTransaction.succes
                selectCommand.idTransaction = newTransaction.id
                selectCommand.save()
                print(selectCommand.paid)
                print(selectCommand.idCreditCard)
                print(selectCommand.idTransaction)
                return True
            #return redirect(url_for('getCommande',order_id = selectCommand.id))#payement avec success
            
            
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False

def Payement(selectCommand,data,global_queue,list_taks_id,list_order_id): # cette fonction permet de faire le paiement de la commande
    #vérifier que il y a les informations de clients
    try:
        client = Client.get_by_id(selectCommand.idClient)
        #vérifier si la commande a ete deja paye ou pas
        if(selectCommand.paid==True):
            error = ViewError("order",422,"already-paid","La commande a été déjà payé")
            return error.response()
        #création des données pour l'API
        amountCharged = selectCommand.total_price + selectCommand.shipping_price
        params = {"credit_card":data["credit_card"],"amount_charged":amountCharged}
        jsonParams = json.dumps(params).encode("utf-8") #le JSON à envoyé

        #effectuer la transaction du payement avec l'API en arriere plan
        task = global_queue.enqueue(PayementIntegration,selectCommand,jsonParams,amountCharged)
        list_taks_id.append(task.id)#mettre dans une liste l'id de task et du commande
        list_order_id.append(selectCommand.id)
        #return PayementIntegration(selectCommand,jsonParams)
        return redirect(url_for('getCommande',order_id = selectCommand.id))#si les premiers verifications sont en succes, on va retourner directement une reponse en attendant la tache en arriere plan
    except Exception as e:
        error = ViewError("order",422,"missing-fields","Les informations du client sont nécéssaire avant d'appliquer une carte credit")
        return error.response()

def OperationChoice(order_id,data,global_queue,list_taks_id,list_order_id):
    #2eme étape: est ce que la commande éxiste ou pas:
    try:
        selectCommand = Commande.get_by_id(order_id)
        #3eme etape: assurer que soit on obtient seulement l'information du client soit la carte de credit
        if(len(data)>1):
            erreur = ViewError("order",422,"lof-of-contents","Une seule action par opération est acceptée")
            return erreur.response()
        
        if(next(iter(data)) == "order"):
            return UpdateClient(selectCommand,data)
        else:
            return Payement(selectCommand,data,global_queue,list_taks_id,list_order_id)
    except:
        erreur = ViewError("order",404,"missing-order","La commande n\'éxiste pas")
        return erreur.response()



def InsertProduct(data): #permet d'insérer une product dans la table product
    Produit.create(
        id = data["id"],
        name = data["name"],
        in_stock = data["in_stock"],
        description = data["description"],
        price = data["price"],
        weight = data["weight"],
        image = data["image"]
    )

def InsertPanier(data): #permet d'inserer des produits dans une commande
    Panier.create(
        idCommande = data["idCommande"],
        idProduit = data["idProduit"],
        quantity = data["quantity"]
    )

def InsertCommand(data):#permet d'insérer une commande dans la table commande et retourne la commande inserer
    NewCommand = Commande.create(
        shipping_price = data["shipping_price"],
        total_price = data["total_price"],
        paid = False
    )
    return NewCommand #retourne la nouvelle commande

def InsertClient(email,information):

    newClient = Client.create(
        email = email,
        country = information["country"],
        adress = information["address"],
        postal_code = information["postal_code"],
        city = information["city"],
        province = information["province"]
    )
    return newClient

def InsertCreditCard(data):#permet d'insérer une nouvelle carte credit
    NewCredit = CreditCard.create(
        name = data["name"],
        first_digits = data["first_digits"],
        last_digits = data["last_digits"],
        expiration_year = data["expiration_year"],
        expiration_month = data["expiration_month"]
    )
    return NewCredit

def InsertTransaction(data):#permet d'insérer une nouvelle transaction
    newTransaction = Transaction.create(
    idSucces = data["id"],
    succes = data["succes"],
    amount_change = data["amount_charged"],
    code = data['code'],
    name = data['name']
    )
    return newTransaction


def testAffichage(data):
    print("Le woker a bien fonctionne, felicitation")
    return data