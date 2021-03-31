from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from random import randint
from pymongo import MongoClient

import hashlib
import uuid
import datetime
import time
import json

app = Flask(__name__)
api =Api(app)

client = MongoClient("mongodb://db:27017")
#client = MongoClient("mongodb://localhost:27017")

db = client.JuloWallet
customers = db["customers"]
wallets = db["wallets"]
deposits = db["deposits"]
withdrawals = db["withdrawals"]

def checkHeaderData(headers, functionName):

    if (functionName == "wallet"):
        try:
            #check is the token in the customers collection
            token = headers.get("Authorization")

            customer_xid = customers.find({
                "token": token
            })[0]["customer_xid"]
        except IndexError:
            return 301
        except Exception as e:

            return 301

            #will find a way to use exception handling in Python next time
class Init(Resource):
    def post(self):
        #Step one to get the posted data by the user
        postedData = request.get_json()

        #Get the data
        customer_xid = postedData["customer_xid"]

        #later on will be changed using JWT token
        ts = str(time.time())
        password = " salt "+customer_xid+ts

        token = "Token "+str(hashlib.md5(password.encode("utf-8")).hexdigest())
        customers.insert({
            "customer_xid": customer_xid,
            "token": token,
        })

        #create a wallet to be activated next using EnableWallet api
        wallet_id = str(uuid.uuid1())
        wallet = {
            "id": wallet_id,
            "owned_by": customer_xid,
            "status": "disable",
            "enabled_at": 0,
            "balance": 0
        }
        wallets.insert(wallet)

        #prepare the response
        retJson = {
            "data":{
                "customer_xid" : customer_xid,
                "token" : token},
            'Status Code' : "success"
        }
        return jsonify(retJson)

class EnableWallet(Resource):
    def post(self):

        #get the posted data by the user
        postedData = request.get_json()

        #get header data :
        headers = request.headers

        #check posted data
        status_code = checkHeaderData(headers, "walet")

        token = headers.get("Authorization")
        #if status_code !=200
        customer_xid = customers.find({
            "token": token
        })[0]["customer_xid"]

        #update wallet
        ct = str(datetime.datetime.now())
        wallets.update({
            "owned_by":customer_xid
        }, {
            "$set":{
                "status": "enabled",
                "enabled_at": ct
                }
        })

        #prepare the response with the wallet
        wallet = dict(wallets.find({"owned_by":customer_xid},{"_id":0,"reference_id":0})[0])

        retJson = {
            "Status" : "success",
            "data":{
                "wallet": wallet}
        }

        return jsonify(retJson)

class ViewWallet(Resource):
    def get(self):
        #get the posted data by the user
        postedData = request.get_json()

        #get header data :
        headers = request.headers

        #check posted data
        status_code = checkHeaderData(headers, "walet")

        token = headers.get("Authorization")
        #if status_code !=200
        customer_xid = customers.find({
            "token": token
        })[0]["customer_xid"]

        #prepare the response with the wallet
        wallet = dict(wallets.find({"owned_by":customer_xid},{"_id":0,"reference_id":0})[0])
        if (wallet['status']!="enabled"):
            return jsonify({"status":301})
        retJson = {
            "Status" : "success",
            "data":{
                "wallet": wallet}
        }

        return jsonify(retJson)

class DepositWallet(Resource):
    def post(self):

        #get the posted data by the user
        postedData = request.get_json()
        amount = postedData["amount"]
        reference_id = postedData["reference_id"]

        #get header data :
        headers = request.headers

        #check posted data
        status_code = checkHeaderData(headers, "deposits")

        token = headers.get("Authorization")
        #if status_code !=200
        customer_xid = customers.find({
            "token": token
        })[0]["customer_xid"]

        #insert deposit ammount
        ct = str(datetime.datetime.now())
        deposit_id = str(uuid.uuid1())
        deposit = {
            "id": deposit_id,
            "deposited_by": customer_xid,
            "status": "success",
            "deposited_at": ct,
            "amount": amount,
            "reference_id": reference_id
        }
        deposits.insert(deposit)

        # add amount to balance
        str_balance = wallets.find({"owned_by":customer_xid})[0]['balance']
        new_balance = int(str_balance) + amount

        # Wallet update balance
        wallets.update({
            "owned_by":customer_xid
        }, {
            "$set":{
                "balance": new_balance
                }
        })

        #prepare the response showing balance in the wallet
        wallet = dict(wallets.find({"owned_by":customer_xid},{"_id":0,"reference_id":0})[0])
        dict_deposit = dict(deposits.find({"id":deposit_id},{"_id":0})[0])

        retJson = {
            "Status" : "success",
            "data":{
                "deposit": dict_deposit,
                "wallet": wallet
                }
        }

        return jsonify(retJson)

class WithdrawalWallet(Resource):
    def post(self):

        #get the posted data by the user
        postedData = request.get_json()
        amount = postedData["amount"]
        reference_id = postedData["reference_id"]

        #get header data :
        headers = request.headers

        #check posted data
        status_code = checkHeaderData(headers, "withdrawal")

        token = headers.get("Authorization")
        #if status_code !=200
        customer_xid = customers.find({
            "token": token
        })[0]["customer_xid"]

        #insert deposit ammount
        ct = str(datetime.datetime.now())
        withdrawal_id = str(uuid.uuid1())
        withdrawal = {
            "id": withdrawal_id,
            "deposited_by": customer_xid,
            "status": "success",
            "deposited_at": ct,
            "amount": amount,
            "reference_id": reference_id
        }
        withdrawals.insert(withdrawal)

        # add amount to balance
        str_balance = wallets.find({"owned_by":customer_xid})[0]['balance']
        new_balance = int(str_balance) - amount

        # Wallet update balance
        wallets.update({
            "owned_by":customer_xid
        }, {
            "$set":{
                "balance": new_balance
                }
        })

        #prepare the response showing balance in the wallet
        wallet = dict(wallets.find({"owned_by":customer_xid},{"_id":0,"reference_id":0})[0])
        dict_withdrawal = dict(withdrawals.find({"id":withdrawal_id},{"_id":0})[0])

        retJson = {
            "Status" : "success",
            "data":{
                "deposit": dict_withdrawal,
                "wallet": wallet
                }
        }

        return jsonify(retJson)

api.add_resource(Init, '/api/v1/init')
api.add_resource(EnableWallet, '/api/v1/wallet')
api.add_resource(ViewWallet, '/api/v1/wallet')
api.add_resource(DepositWallet, '/api/v1/wallet/deposits')
api.add_resource(WithdrawalWallet, '/api/v1/wallet/withdrawals')

if __name__=="__main__":
    app.run(host='0.0.0.0',port='80')
