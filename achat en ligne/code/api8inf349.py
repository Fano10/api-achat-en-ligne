from flask import Flask, jsonify, make_response,request,redirect,url_for,render_template
from MVC.model import *
from MVC.view import ViewAllProducts,ViewCommande,ViewError
from MVC.service import*
from urllib.request import urlopen

app = Flask(__name__)
init_app(app)

global_queue = Queue(connection = get_db_redis())

list_order_id = []
list_taks_id= []
@app.route('/')
def getProduct():
    ligne = Produit.select() 
    response = ViewAllProducts(ligne)
    return response.response()
	
@app.route('/order',methods = ['POST'])
def nouvelleCommande():

    if request.is_json:
        data = request.json
        try:
            dataCommand = data["product"]
            response = InsertCheckCommand(dataCommand)
        except:
            dataCommand = data["products"]
            response = InsertCheckCommandTab(dataCommand)
        return response

@app.route('/order/<int:order_id>',methods=['GET'])
def getCommande(order_id):
    try:#verifier si la commande est au cours du payement
        indice = list_order_id.index(order_id)
        task = global_queue.fetch_job(list_taks_id[indice])#prendre la vraie id du task qui correspond au commande
        if not task.is_finished: # si la tache n'est pas encore fini
            return  make_response('',202) # la tache n'est pas encore termine.
        else:
            list_order_id.pop(indice)#supprimer l'id de la tache lorsque la tache est fini
            list_taks_id.pop(indice)
    except:
        pass
    return GetCommand(order_id,global_queue)

@app.route('/order/<int:order_id>',methods=['PUT'] )
def misAjourCommande(order_id):
    try:#verifier si la commande est au cours du payement
        indice = list_order_id.index(order_id)
        task = global_queue.fetch_job(list_taks_id[indice])#prendre la vraie id du task qui correspond au commande
        if not task.is_finished: # si la tache n'est pas encore fini
            return  make_response('',409) # la tache n'est pas encore termine.
    except:
        pass
    if request.is_json:
        data = request.json
        response = OperationChoice(order_id,data,global_queue,list_taks_id,list_order_id)
        return response
    

@click.command("worker") #commande pour initialiser le worker
@with_appcontext
def rq_worker_command():
    worker = Worker([global_queue],connection = get_db_redis())
    worker.work()

app.cli.add_command(rq_worker_command)

#Point d'entree principale de l'application
if __name__ == '__main__':
    Initialization()#initialisation de l'application et recuperation des donnees
    app.run(host="0.0.0.0")