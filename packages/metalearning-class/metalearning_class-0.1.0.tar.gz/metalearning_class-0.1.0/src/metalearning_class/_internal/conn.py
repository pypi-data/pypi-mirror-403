import requests as req
import json

local = False

if local:
    mtl_api_ulr = 'http://localhost:11500'
    sofon_api_url = 'http://localhost:11501'
else:
    mtl_api_ulr = 'https://mtl.sofon.io'
    sofon_api_url = 'https://api.sofon.io'



class Conn:

    def __init__(self):
        self.token = None
    

    def get_headers(self):
        try:
            headers = {
            "Authorization": f"Bearer {self.token}"  # Replace 'Bearer' if your API uses a different scheme
            }
        except:
            print("You are not logged in, please make the login using the login function")
        return headers


    def insertion(self, body):
        #res = req.post(url="http://192.168.15.49:7501/topologies/create", json=body)
        headers = self.get_headers()
        res = req.post(url= mtl_api_ulr + "/topologies/create", headers=headers,json=body)
        print("Response: ", res.text)
        if res.status_code == 200:
            print("Topology successfully inserted")
        else:
            print("Error na insercao " + str(res.status_code))
        return res.json()
    

    def insertion_funchp(self,body):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/create", json=body)
        headers = self.get_headers()
        res = req.post(url= mtl_api_ulr + "/topologies/hyperparameters/create", headers=headers,json=body)
        print("Response: ", res.text)
        if res.status_code == 200:
            print("Hyperparameters successfully inserted")
        else:
            print("Error na insercao " + str(res.status_code))
        next


    def get_any_field(self,body):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/getbyanyfield", json=body)
        headers = self.get_headers()
        res = req.post(url= mtl_api_ulr + "/topologies/hyperparameters/getbyanyfield",headers=headers, json=body)
        if res.status_code == 200:
            print("Sucess")
        else:
            print("Error " + str(res.status_code))
        return res.json()
    

    def import_model(self,data):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/getbyanyfield", json=body)
        headers = self.get_headers()
        res = req.get(url= mtl_api_ulr + "/topologies/read_by_nameanduser_or_id",headers=headers, params=data)
        if res.status_code == 200:
            print("Model sucessfully imported")
        else:
            print("Error " + str(res.status_code))
        return res.json()
    

    def insert_results(self,result_data):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/getbyanyfield", json=body)
        headers = self.get_headers()
        res = req.post(url= mtl_api_ulr + "/topologies/insert_accuracy_results",headers=headers, json = result_data)
        if res.status_code == 200:
            print("Results successfully inserted")
        else:
            print("Error " + str(res.status_code))
        return res.json()
    

    def import_train_data(self,data):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/getbyanyfield", json=body)
        headers = self.get_headers()
        res = req.get(url= mtl_api_ulr + "/data-meta-data/get-train-data",headers=headers, params=data)
        if res.status_code == 200:
            print("Train data sucessfully imported")
        else:
            print("Error " + str(res.status_code))
        return res.json()
    

    def import_test_data(self,data):
        #res = req.post(url="http://192.168.15.49:7501/topologies/hyperparameters/getbyanyfield", json=body)
        headers = self.get_headers()
        res = req.get(url= mtl_api_ulr + "/data-meta-data/get-test-input-data",headers=headers, params=data)
        if res.status_code == 200:
            print("Test data sucessfully imported")
        else:
            print("Error " + str(res.status_code))
        return res.json()
    

    """
    funcao responsavel por aciona uma funcao do back-end capaz de prever o melhor modelo e topologia para uma determinada task
    """
    #soon it will be possible to use this predict model!!!
    def predict_model(self, task):
        return


    # added the functions here,for website connection

    def get_token(self,username, password):
        urll = sofon_api_url + "/token"
        form_data = {
            'username': username,
            'password': password
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        res = req.post(urll, data=form_data, headers=headers)
        
        if res.status_code == 200:
            print("\nLogin sucessfull\n")
            data = res.json() 
            self.token = data['access_token']
            return data
        else:
            print("Error getting token " + str(res.status_code) + " - Check your credentials")


    def get_task_meta_data_from_challenge(self,taskname):
        form_data = {
            "Taskname" : taskname
        }
        headers = {
            "Authorization": f"Bearer {self.token}",  # Replace 'Bearer' if your API uses a different scheme
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        res = req.post(url= sofon_api_url + f"/participate_challenge", headers=headers,data=form_data)

        if res.status_code == 200:
            print("Sucess getting task meta data")
            return res.json() 
        else:
            print("Error getting task meta data:" + str(res.status_code))

