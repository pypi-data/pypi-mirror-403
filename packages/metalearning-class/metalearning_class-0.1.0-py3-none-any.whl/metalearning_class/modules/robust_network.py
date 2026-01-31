# Pensar em implementar em C ou alguma linguagem mais rapida, como julia

from netrc import netrc
import numpy as np
import pandas as pd
import random 
import math
import matplotlib.pyplot as plt

class RNAPNL():
    #formula: X' = W0*S(V0*Z), tambem eh preciso pensar no tetha
    
    def __init__(self,ninput,hidden_layer,B_cte,K_cte,A_cte_negative,Yw,aw,Yv,av, hyperparameters = None):
        
        hyperparameters = { #definir quais serao os parametros ideais
            'hyperparameters': {
                'num_layers' : 2,
                'n_input' : ninput,
                'hidden_layer': hidden_layer,
                'cte_B': B_cte,
                'cte_K': K_cte,
                'cte_A': A_cte_negative,
                'cte_Yw': Yw,
                'cte_aw': aw,
                'cte_Yv': Yv,
                'cte_av': av
            }
        } 
        #adicionar metadado de topologias aqui
        self.erros = [] 
        self.classes = []
        
        self.nmr_neuronios_camada1 = hidden_layer
        self.nmr_neuronios_camada2 = ninput 
        self.nmr_neuronios_camada3 = ninput
        self.ninput = ninput + ninput + 1
        
        self.Yw = Yw
        self.aw = aw
        
        self.Yv = Yv
        self.av = av
        
        self.B = np.zeros((ninput,ninput)) #matriz diagonal com todos os termos positivos
        for i in range(0,len(self.B)):
            self.B[i,i] = B_cte*random.randint(1,1)
        self.K = np.zeros((ninput,ninput))
        for i in range(0,len(self.K)):
            self.K[i,i] = K_cte*random.randint(1,1)
        self.A = np.zeros((ninput,ninput)) #matriz diagonal com todos os termos negativos
        for i in range(0,len(self.A)):
            self.A[i,i] = -A_cte_negative*random.randint(1,1)
        
        self.V0 = np.random.randint(-100,100, size = (2*self.nmr_neuronios_camada1+1,self.ninput))/2017321
        self.V = self.V0.copy()
        
        self.W0 = np.random.randint(-100,100, size = (self.nmr_neuronios_camada2,2*self.nmr_neuronios_camada1+1))/2017321 # a ultima parte nao pode ser alterada
        self.W = self.W0.copy()
        
        self.V = self.V.astype(np.longdouble)
        self.V0 = self.V0.astype(np.longdouble)
        self.W = self.W.astype(np.longdouble)
        self.W0 = self.W0.astype(np.longdouble)
        self.A = self.A.astype(np.longdouble)
        self.B = self.B.astype(np.longdouble)
        #self.K = 10
        self.u = np.zeros(ninput) #estado atual
    
    def regressor(self,X):
        
        aux = []
        if len(X) > 1:
            for E in X:
                 if E > 0:
                     aux.append(E)
                 else:
                     aux.append(0)
                #aux.append((1/2)/(1+1*math.exp(-E)) + 0)
                #aux.append(E**(-2))
        else:
                #aux.append((1/2)/(1+1*math.exp(-X)) + 0)
                 if X > 0:
                     aux.append(X)
                 else:
                     aux.append(0)
                #aux.append(X**(-2))
            #aux.append(math.sin(E))
        return(np.asarray(aux))
    
    def dregressordx(self,X):
        aux = []
        for E in X:
            #aux.append((self.regressor(np.asarray([E])) * (1 - self.regressor(np.asarray([E])))))
            if E > 0:
                aux.append(1)
            else:
                aux.append(0)
            #aux.append(-2*X)
            #aux.append(math.cos(E))
        return(np.asarray(aux))
    
    #Xi is the prediction with 255:1 shape, Y is the expected result, X is the input without treatment
    #and u is the state prediction
    def ajuste_pesos(self,Y,X,Xi,u):
        
        Z = np.append(X,u)
        Z = np.append(Z,np.asarray([1]))
        Xtio_ = Y - Xi
        
        regressord = self.dregressordx(np.dot(self.V,Z))
        
        aux = []
        for i in range(0,len(regressord)):
            temp = np.zeros(2*self.nmr_neuronios_camada1+1)
            #for j in range(0,len(temp)):
                #temp[j] = regressord[i]
            temp[i] = regressord[i]
            aux.append(temp)
        regressord = np.asarray(aux)

        if type(Xtio_) != int:
      
            self.W = self.W + (-self.Yw *(self.aw * np.linalg.norm(np.array([Xtio_]), 'fro') * (self.W - self.W0) +
                    np.dot(self.B,np.dot(self.K,np.dot(np.asarray([Xtio_]).T,np.asarray([self.regressor(np.dot(self.V,Z))]))))
            #         - np.dot(self.B, np.dot(np.asarray([self.K*Xtio_]).T,np.asarray([np.dot(regressord,np.dot(self.V,Z))])))))
                    - np.dot(self.B, np.dot(np.asarray([np.dot(self.K,Xtio_)]).T,np.asarray([np.dot(regressord,np.dot(self.V,Z))])))))
                            
            
            self.V = self.V + -self.Yw *(self.aw * np.linalg.norm(np.array([Xtio_]), 'fro') * (self.V - self.V0) + 
                    #np.dot(regressord,np.dot(self.W.T,np.dot(self.B,np.dot(self.K*np.asarray([Xtio_]).T,np.asarray([Z]))))))
                    np.dot(regressord,np.dot(self.W.T,np.dot(self.B,np.dot(np.asarray([np.dot(self.K,Xtio_)]).T,np.asarray([Z]))))))
        else:
            self.W = self.W + (-self.Yw *(self.aw * abs(Xtio_) * (self.W - self.W0) +
                    np.dot(self.B,np.dot(self.K,np.dot(np.asarray([Xtio_]).T,np.asarray([self.regressor(np.dot(self.V,Z))]))))
            #         - np.dot(self.B, np.dot(np.asarray([self.K*Xtio_]).T,np.asarray([np.dot(regressord,np.dot(self.V,Z))])))))
                    - np.dot(self.B, np.dot(np.asarray([np.dot(self.K,Xtio_)]).T,np.asarray([np.dot(regressord,np.dot(self.V,Z))])))))
                            
            
            self.V = self.V + -self.Yw *(self.aw * abs(Xtio_) * (self.V - self.V0) + 
                    #np.dot(regressord,np.dot(self.W.T,np.dot(self.B,np.dot(self.K*np.asarray([Xtio_]).T,np.asarray([Z]))))))
                    np.dot(regressord,np.dot(self.W.T,np.dot(self.B,np.dot(np.asarray([np.dot(self.K,Xtio_)]).T,np.asarray([Z]))))))
    def Xi(self,X,u): 
        Z = np.append(X,u)
        Z = np.append(Z,np.asarray([1]))
        return(-np.dot(self.A,(u)) - np.dot(self.B,np.dot(self.W,self.regressor(np.dot(self.V,Z)))))
    
    def train(self,erro_min, X, Y, from_x = True):
        count = 1
        epoch = 1
        erro = 0
        frobenius_variation = []
        while(True):
            #Y,X,Xi,u
            erro = 0
            print('\n------------ epoch ' + str(epoch) + ' ------------\n')
            for i in range(0,len(X)):   
                print("\r", str(i) + '----- ' + str(abs(self.V).mean()), end="")
                if from_x:
                    self.u = X[i]
                du = self.Xi(X[i],self.u)
                prediction = self.u + du
                self.ajuste_pesos(Y[i],X[i],prediction,self.u)
                self.u = prediction
                erro = erro + np.sum(abs(Y[i] - prediction))/len(Y[i]) #posso incluir aqui no meio um train adversarial para gerar uma outra rede, ou mesmo criar um segundo train para gerar pixel - to - pixel
                self.erros.append([i,erro])
                frobenius_variation.append(np.linalg.norm(self.V0, 'fro'))
                #self.classes.append([Y[i].sum(),prediction.sum()])
                #if (i+1) % 100 == 0:
                    #print('erro temp ' + str(i+1) + ' ' + str(erro/(i+1)))
            print("\n")
            print(erro/len(X)) #configurar epochs para ser capaz de capturar o historico de aprendizado
            epoch = epoch + 1
            if erro/len(X) < erro_min:
                break
            return [erro/len(X),frobenius_variation]

    def define_u(self,u):
        self.u = u
            
    def predict(self,X):
        du = self.Xi(X,self.u)
        prediction = self.u + du
        self.u = prediction
        return prediction

class Robust_classifier():
    #problema para mapear os dados, criando por aqui. Qual a solucao?
    def __init__(self,number_classifiers,ninput,hidden_layer,B_cte,K_cte,A_cte_negative,Yw,aw,Yv,av, hyperparameters = None):
        hyperparameters = { #definir quais serao os parametros ideais
            'hyperparameters': {
                'num_classifiers' : number_classifiers,
                'num_layers' : 2,
                'n_input' : ninput,
                'hidden_layer': hidden_layer,
                'cte_B': B_cte,
                'cte_K': K_cte,
                'cte_A': A_cte_negative,
                'cte_Yw': Yw,
                'cte_aw': aw,
                'cte_Yv': Yv,
                'cte_av': av
            }
        } 
        self.classifiers = []
        for i in range(0,number_classifiers):
            self.classifiers.append(RNAPNL(ninput,hidden_layer,B_cte,K_cte,A_cte_negative,Yw,aw,Yv,av, hyperparameters))

    def train(self,erro_min, X, Y, classe, from_x = True):
        result = []
        #criar uma especie de enumerate para as classes Y
        for i in range(0,len(X)):
            model = self.classifiers[int(classe[i])]
            result.append(model.train(erro_min, X[i], Y[i], from_x))
            #precisa organizar o X e o Y
        return result
    
    def predict_class(self,X):
        erro_min = np.Inf
        classifier = -1
        for i in range(0,len(self.classifiers)):
            model = self.classifiers[i]
            erro = 0
            for seq in range(0,len(X)):
                if seq == (len(X)-1):
                    break
                model.define_u(X[seq])
                prediction = model.predict(X[seq])
                erro = erro + np.sum(abs(X[seq+1] - prediction))/len(X[i]) #problema de degradacao do vetor
            if erro < erro_min:
                erro_min = erro
                erro = 0
                classifier = i
        return classifier
        