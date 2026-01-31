"""
documentacao geral e instrucoes

- Objetivo principal da classe de meta-learning
    - Gerenciar e centralizar o tratamento de meta-dados
    - Gerenciar e centralizar os servicos de meta-learning do lado do usuario
    - Gerencair e centralizar treinamentos tunados com meta-learning (Revisitar esse objetivo)

- *** essa arquitetura abaixo esta sob avaliacao 
A classe de meta-learning NAO DEVE SER RESPONSAVEL PELO PREENCHIMENTO DE INFORMACOES DE META-DADOS
    - As sub-classes, responsaveis por gerir os modelos existentes: Transformers, redes densas, CNN, redes robustas e metamodelo
    devem ser responsaveis por preencher os seus proprios meta-dados e informar a classe de meta-learning.
    - User Request -> Mtclass pergunta a sub-classe quais sao os meta-dados -> sub-class responde com os meta-dados 
"""

##remember:
#add counting of hyperparameters in all models...

import tensorflow as tf
from cmath import inf

# from fastapi import FastAPI
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from si_prefix import si_format
# import tracemalloc
# import keras
from keras.models import Model, load_model
from keras.layers import Dense, Input
import keras.layers as layers
from keras.callbacks import EarlyStopping
from keras.metrics import mean_squared_error

from metalearning_class.modules.transformer import Transformer_gerenciator
from metalearning_class.modules.robust_network import RNAPNL, Robust_classifier
import metalearning_class.modules.functions as f

import tracemalloc
from si_prefix import si_format
from dill.source import getname
from metalearning_class._internal.conn import Conn
import random
import os
from tensorflow.keras.models import model_from_json
import numpy as np
import time
import json
import subprocess
import platform

# set to run on CPU


# --------------------------------------------------  Metalearning --------------------------------------------------
# "Tipo": "DNN", ok
# "geracao": 0,  # aplicar aprendizado genetico
# "versao": 1,
# "loss_function": "mean_squared_error",
# "optimizer": "adam",
# "nome": "preditor-espectro-de-frequencia-meta-materiais",
# "hyperparameters": {"camadas": [200, 200, 301], "numero_camadas": 3},


class mtl_class:
    def __init__(self, gpu=False):
        """
        Initialize the meta-learning controller instance.

        Parameters
        ----------
        gpu : bool, optional
            If False, forces CPU execution by setting CUDA_VISIBLE_DEVICES='-1'.
            If True, leaves GPU settings to the environment. Default is False.

        Returns
        -------
        None

        Notes
        -----
        This constructor initializes internal state that is used throughout the
        object's lifecycle (training history, metadata containers, backend connection,
        default hyperparameter containers, etc.). The object does not construct a
        Keras model here — the network topology is created incrementally by calls to
        `add_input` and `add_dense`, or by using a ready-made model via `load_keras_model`.
        
        Examples
        --------
        >>> ml = mtl_class(gpu=False)
        """
        
        if not gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        # self.model = Model()
        # self.model_type = model._name.split("_")[0]
        self.generation = 1
        self.version = 1
        self.history = None
        self.best_history = None
        self.short_theme = None
        self.peak_memory = None
        self.loss = None
        self.loss_value = None
        self.metadata = None
        self.output = None
        self.task_meta_features = None
        self.topology_metadata = None
        self.results = None
        self.patience = None
        self.batch_size = None
        self.epochs = None
        self.epochs_used = None
        self.hyperparemeters = None
        self.imported = False
        self.conn = Conn()

    # dividir em duas funcoes
    # def add_task(self, task_name, task_metadata, search=True):
    # se a pessoa ja estiver trabalhando em cima de um modelo?
    # if search:
    #     bool = api.there_exists(
    #         task_name, task_metadata
    #     )  # se nao existir criar a task no banco de dados
    #     if bool:
    #         return
    #     api.competition_function(
    #         task_name, task_metadata
    #     )  # deve retornar as melhor topologia

    def clear_console(self):
        try:
            if platform.system() == "Windows":
                subprocess.call('cls', shell=True)
            else:
                subprocess.call('clear', shell=True)
        except:
            print("\n" * 100)


    #can have a login to check the level of acess from the user
    def set_user(self,username,password):
        self.user = username
        self.password = password #insert here some kind of chriptograhy, for example

    def add_topology_name(self,name):
        self.topology_name = name

    #***
    #a class to deal with the hyperparameters could be created in the future

    #to make the gerentitation of the tests it is possible to think in a testname that demands uniquenes alongside with function_name
    # but it can restrict the information insertion on the data bank... 
    #at the same time, if it is not restricted, the queries can present a difficult to use the data, as equal names can
    #lead to different data structures for diferent data
    #If the username, for example, is used to guarante uniquenes, it do not resolve the problem of combination of multiple task names
    #what is the solution for that???
    #the uniqueness can be considered as union of hyperameter_name, function_name and test_name, 
    #and possibily the queries will have to have a filter, but equal tests will have equal ids to fast queries
    #a second id can be created to classify similarities and possibilities of equal queries... for example
    def insert_function_hyperparameter(self,
                                    access,
                                    hyperparameter_name,
                                    shape,
                                    hyperparameter_data, #not mandatory
                                    function,
                                    function_name,
                                    data,
                                    accuracy,
                                    testname,
                                    testid,
                                    sequence,
                                    kind_of_analysis,
                                    data_input = None,
                                    linked_model = None, #not mandatory
                                    compatibility = None,
                                    nested_classes = None # not mandatory; indicates tests and hyperparameter that are classified within the same classes, therefore is a vector... can give very good combinations, and is a test
                                    ):
        #pensar na necessidade e nas conexoes dos modelos voltados para tasks, ou nao
        #e na combinacao de modelos atraves de varios hyperparametros e suas coletas de dados
        self.hyperparameter_function_learning = {
                        "user" : self.user,
                        "access" : access,
                        "hyperparameter_name" : hyperparameter_name,
                        "shape": shape,
                        "hyperparameter_data": hyperparameter_data,
                        "function" : function,
                        "function_name": function_name,
                        "data": data,
                        "accuracy": accuracy,
                        "testname": testname,''
                        "testid" : testid,
                        "sequence" : sequence,
                        "kind_of_analysis" : kind_of_analysis,
                        "linked_model" : linked_model, 
                        "compatibility" : compatibility,
                        "nested_classes": nested_classes,
                        "data_input": data_input
                        }
        self.conn.insertion_funchp(self.hyperparameter_function_learning)
        next
    
    def get_hyperparameters_with_any_fields(self,fields_and_values_query, target_field, target_shape):
        self.hyperparameters_with_any_fields_body = {
            "fdquery" : fields_and_values_query,
            "target_field": target_field,
            'target_shape': target_shape
        }
        return self.conn.get_any_field(self.hyperparameters_with_any_fields_body)

    def insert_task(
        
        
        self,
        taskid,
        user,
        kind,
        description,
        data,
        accuracy_parameters,
        taskname,
        theme,
        key_words=None,
        body_defining=None #ideia: Criar funcao que cria um identificador facil para fazer buscas da task a partir dos dados que esta possui ---> outra solucao foi implementada no momento, criar documento para mapear ideias e direcoes
    ):
        """
        Register task metadata inside the mtl_class instance.

        Parameters
        ----------
        taskid : str or int
            Unique identifier for the task/challenge (e.g., challenge id).
        user : str
            Owner or author of the task.
        kind : str
            Task category, e.g. "DNN" or "DNN Genetica".
        description : str
            Human-readable description of the task.
        data : str
            Path or data-link associated with the task (for example "data/heatsense.csv").
        accuracy_parameters : str
            Descriptor of evaluation metric used for the task (e.g. "mean_squared_error").
        taskname : str
            Short name used to reference the task in results/DB.
        theme : str
            Macrocontext / theme for grouping tasks (e.g. "previsao de series temporais").
        key_words : list, optional
            Optional list of keywords/tags.
        body_defining : str, optional
            Optional extended JSON/text describing the task.

        Returns
        -------
        None

        Notes
        -----
        The repository examples sometimes call this API with different argument names
        (Portuguese aliases such as 'tipo' -> kind, 'descricao' -> description,
        'dados' -> data, 'parametros_de_acuracia' -> accuracy_parameters,
        'name' -> taskname, 'macrocontexto' -> theme). The canonical parameter names
        for the method are those listed above.

        Examples
        --------
        >>> ml.insert_task(
        ...     taskid=34,
        ...     user="team",
        ...     kind="DNN",
        ...     description="Previsão de temperaturas médias (HeatSense)",
        ...     data="data/heatsense.csv",
        ...     accuracy_parameters="mean_squared_error",
        ...     taskname="predictionheatsense",
        ...     theme="climate_forecasting"
        ... )
        """

        self.task_meta_features = {
            "taskid" : taskid,
            "taskname" : taskname,
            "theme": theme,
            "User": user,
            "Kind": kind,
            "Description": description,
            "Input_dimensions": None, # verify necessity
            "Output_dimensions": None, # verify necessity
            "Data": data,
            "Accuracy_parameters": accuracy_parameters,
            "Key_words" : key_words,
            "body_defining" : body_defining
        }
        self.task_name = taskname
        self.taskid = taskid
        self.macrocontext = theme #think on changing the macrocontext or add it in the future
    


       #-------------functions getted from website api----=0-----------------------------------------------------------------------------

    def login(self, username: str, password: str) -> None:
        """
        Authenticate user in Sofon and store session credentials.

        This method clears the console, sets the username and password,
        and requests an authentication token from the server.

        Args:
            username (str): The  Sofon username used for authentication.
            password (str): The Sofon password used for authentication.

        Returns:
            None
        """
        self.clear_console()
        self.user = username
        self.password = password  # TODO: consider encrypting password before storing.
        
        token_data = self.conn.get_token(username, password)




    def subscribe_and_get_task(self, taskname, data_location = './data'):  
        print('==============================================')
        task_data = self.conn.get_task_meta_data_from_challenge(taskname)
        
        
        #we should fix the challenge_id here ans taskname...
        self.insert_task(
            taskid=task_data.get("Challenge_id"),
            user=task_data.get("Username"),  
            kind=task_data.get("Categories"),
            description=task_data.get("Description"),
            data=task_data.get("Datalink"),
            accuracy_parameters=task_data.get("Accuracy_parameter"),
            taskname=task_data.get("Taskname"),
            theme=task_data.get("Theme"),
            key_words=None, 
            body_defining=None  
        )
        # printing this on
        print("")
        print(f"Taskname: {task_data.get('Challenge_id')}")
        print(f"Challenge by: @{task_data.get('Username')}")
        print(f"Categories: {', '.join(task_data.get('Categories'))}")
        print(f"Title: {task_data.get('Taskname')}")
        print(f"Theme: {task_data.get('Theme')}")
        print('==============================================')
        self.task_name = task_data.get("Challenge_id")
        self.taskid = task_data.get("Taskid")

        

        self.train_data = self.load_train_data(taskname=self.task_name,taskid= self.taskid, local_path=data_location)
        return self.train_data



    # ---------------------------------=0-----------------------------------------------------------------------------




    def add_input(self, shape, name=None):
        """
        Declare the model input layer and register input shape in task metadata.

        Parameters
        ----------
        shape : tuple
            Input shape (for example (n_features,) for tabular data).
        name : str, optional
            Optional name for the Input layer.

        Returns
        -------
        None

        Raises
        ------
        Exception
            If `task_meta_features` is not set (task must be registered via insert_task
            before adding model input).

        Examples
        --------
        >>> ml.add_input((10,))
        """
        
        if self.task_meta_features is None:
            exception = "the task was not defined. Please, insert the task_meta_data before define the model."
            raise Exception(exception)

        self.input = Input(shape=shape, name=name)
        self.stacked_layers = self.input

        self.task_meta_features["Input_dimensions"] = shape
        return
    
    def add_input_shape(self,shape,name=None):
        self.task_meta_features["Input_dimensions"] = shape
        return

    def add_output_shape(self,shape):
        self.task_meta_features["Output_dimensions"] = shape
        return #we can obligate the user to add the output dimensions in order to send the information
    #or receive it from the task (but we would have to check if carefully on insertion of the task)

    def add_dense(
        self,
        units,
        activation="linear",
        kernel_regularizer=None,
        kernel_initializer=None,
    ):
        """
        Add a Dense (fully-connected) layer to the current model stack.

        Parameters
        ----------
        units : int
            Number of neurons (output dimension) for this dense layer.
        activation : str or callable, optional
            Activation function name or callable (e.g., "relu"). Default: "linear".
        kernel_regularizer : keras.regularizers.Regularizer, optional
            Regularizer to apply on the layer kernel.
        kernel_initializer : keras.initializers.Initializer, optional
            Kernel initializer instance or name.

        Returns
        -------
        None

        Notes
        -----
        The method appends a Dense layer to the internal sequential construction
        (applies layer to `self.stacked_layers`) and updates `task_meta_features[
        "Output_dimensions"]` with the provided `units`. Use `add_input` first
        to set the input layer.

        Examples
        --------
        >>> ml.add_dense(128, activation="relu")
        """
        
        layer = Dense(
            units,
            activation=activation,
            kernel_regularizer=kernel_regularizer,
            kernel_initializer=kernel_initializer,
        )
        self.stacked_layers = layer(self.stacked_layers)

        self.task_meta_features["Output_dimensions"] = units

        return

    def add_transformer(self,num_layers,d_model,num_heads,dff,pe_input,pe_target,input_vocab_size,target_vocab_size,words=True):
        self.model = Transformer_gerenciator(
                        num_layers = num_layers, 
                        d_model = d_model, 
                        num_heads = num_heads, 
                        dff = dff,
                        pe_input=pe_input, 
                        pe_target=pe_target,
                        words = words,
                        input_vocab_size= input_vocab_size,
                        target_vocab_size = target_vocab_size,
                        task_meta_features = self.task_meta_features,
                        hyperparameters=self.hyperparemeters
                    )

    def add_robust_rnn(self,ninput,hidden_layer,B_cte,K_cte,A_cte_negative,Yw,aw,Yv,av):
        self.model = RNAPNL(ninput = ninput,
                            hidden_layer = hidden_layer,
                            B_cte = B_cte,
                            K_cte = K_cte,
                            A_cte_negative = A_cte_negative,
                            Yw = Yw,
                            aw = aw,
                            Yv = Yv,
                            av = av, 
                            hyperparameters = self.hyperparemeters)

    def add_Robust_classifier(self,number_classes,ninput,hidden_layer,B_cte,K_cte,A_cte_negative,Yw,aw,Yv,av):
        self.model = Robust_classifier(
                            number_classifiers=number_classes,
                            ninput = ninput,
                            hidden_layer = hidden_layer,
                            B_cte = B_cte,
                            K_cte = K_cte,
                            A_cte_negative = A_cte_negative,
                            Yw = Yw,
                            aw = aw,
                            Yv = Yv,
                            av = av, 
                            hyperparameters = self.hyperparemeters)

    def load_keras_model(
        self,
        path,
    ):
        return load_model(path)

    #***solucao provisoria sera criar mais de uma funcao para os modelos prontos, porem no futuro, talvez o ideal seja unir tudo
    #nas mesmas funcoes, por exemplo, possuir apenas uma funcao compile
    def compile(
        self,
        loss,
        optimizer,
        metrics,
        model_name,
        generation=None,
        model_type=None,
        genetic_learning=False,
    ):
        """
        Compile the Keras model and populate topology metadata.

        Parameters
        ----------
        loss : str or callable
            Loss function (e.g. "mean_squared_error") or callable loss.
        optimizer : str or keras.optimizers.Optimizer
            Optimizer name or optimizer instance (e.g. "adam").
        metrics : list or None
            List of metric names/callables to track.
        model_name : str
            Human-friendly model / topology name (used in saved metadata).
        generation : int, optional
            Generation index (used by genetic procedures). Default: 0 if not provided.
        model_type : str, optional
            Optional explicit model type label (not typically required).
        genetic_learning : bool, optional
            If True, compile in the genetic-learning context. Default: False.

        Returns
        -------
        None

        Notes
        -----
        - If the instance is not using an imported model (`self.imported` is False),
        the method builds a keras Model from `self.input` and `self.stacked_layers`
        and then compiles it.
        - The method captures model summary output in `self.hyperparemeters` and
        produces an entry `self.topology_metadata` containing the model summary and
        parameter counts (used later when saving/recording the topology).

        Examples
        --------
        >>> ml.compile(loss="mean_squared_error", optimizer="adam", metrics=None, model_name="heatsense_predictor")
        """
        
        if not self.imported:
            if not genetic_learning:
                self.model = Model(inputs=self.input, outputs=self.stacked_layers) #We should add more versatility to user tensorflow better
            self.model.compile(loss=loss, optimizer=optimizer, metrics=metrics)
            self.model_type = "model"

            self.hyperparemeters = []
            self.model.summary(print_fn=lambda x: self.hyperparemeters.append(x))

            if generation:
                next
            else:
                generation = 0

            self.topology_metadata = {
                "Type": self.model_type,
                "generation": generation,  # aplicar aprendizado genetico
                "version": 1,
                "loss_function": loss,
                "optimizer": optimizer,
                "name": model_name,
                # apenas hyperparametros do modelo
                "hyperparameters": {
                                    "summary" : self.hyperparemeters,
                                    "number_of_parameters" : self.model.count_params()
                                    } ,           
            } #it should import all the metadata also when importing a model...
        else:
            self.model.compile(loss=loss, optimizer=optimizer, metrics=metrics)

    
    def compile_transformer(self,loss,optimizer,metrics,model_name,
        generation=None):

        if generation:
            next
        else:
            generation = 0

        self.topology_metadata = {
            "Type": "transformer",
            "generation": generation,  # aplicar aprendizado genetico
            "version": 1,
            "loss_function": getname(loss),
            "optimizer": getname(optimizer),
            "name": model_name,
            # apenas hyperparametros do modelo
            "hyperparameters": self.hyperparemeters,
        }

        self.model.compile(loss_object = loss, optimizer = optimizer, metrics = metrics)

        next

    def compile_robust_rnn(self,model_name,generation=None):
        if generation:
            next
        else:
            generation = 0

        self.topology_metadata = {
            "Type": "Robust_RNN",
            "generation": generation,  # aplicar aprendizado genetico
            "versao": 1,
            "loss_function": 'embeded_robust_adaptation_law',
            "optimizer": 'lyapunov_theory',
            "name": model_name,
            # apenas hyperparametros do modelo
            "hyperparameters": self.hyperparemeters,
        }
        return

    def compile_robust_classifier(self,model_name,generation=None):
        if generation:
            next
        else:
            generation = 0

        self.topology_metadata = {
            "Type": "Robust_RNNs_Classifiers",
            "generation": generation,  # aplicar aprendizado genetico
            "versao": 1,
            "loss_function": 'embeded_robust_adaptationlaw_classifier',
            "optimizer": 'lyapunov_theory',
            "name": model_name,
            # apenas hyperparametros do modelo
            "hyperparameters": self.hyperparemeters,
        }
        return

    def summary(self):
        """
        Print the Keras model summary to stdout.

        This is a convenience wrapper over `self.model.summary()`.

        Returns
        -------
        None

        Examples
        --------
        >>> ml.summary()
        """
        
        self.model.summary()

    def add_callback(self, monitor, patience):
        """
        Create and register an EarlyStopping callback to be used in training.

        Parameters
        ----------
        monitor : str
            Name of the metric to monitor (e.g. "val_loss" or "loss").
        patience : int
            Number of epochs with no improvement after which training will be stopped.

        Returns
        -------
        None

        Notes
        -----
        The method sets `self.patience` and `self.callback` (a keras.callbacks.EarlyStopping
        instance) so that `self.fit()` will use it.

        Examples
        --------
        >>> ml.add_callback(monitor="val_loss", patience=10)
        """
        
        self.patience = patience
        self.callback = EarlyStopping(monitor=monitor, patience=patience)

    #*** adicionando funcao provisoria de fit para o transformer
    #the insertion will have to check, if the topology_name already exists, so we have to update it...
    #verify how to do that
    def fit(self, x, y, epochs, batch_size, validation_split, genetic_learning=False):
        """
        Train the compiled Keras model on provided data.

        Parameters
        ----------
        x : numpy.ndarray or pandas.DataFrame
            Input features used for training.
        y : numpy.ndarray or pandas.DataFrame
            Target values.
        epochs : int
            Maximum number of epochs for training.
        batch_size : int
            Batch size for gradient updates.
        validation_split : float
            Fraction of the training data to be used as validation (Keras-style).
        genetic_learning : bool, optional
            If True, the fit is executed as part of a genetic training loop. Default: False.

        Returns
        -------
        None

        Side effects
        ------------
        - Stores training history in `self.history` (keras History object).
        - Sets `self.batch_size` and `self.peak_memory` (peak memory measured via tracemalloc).
        - If `genetic_learning` is False, aggregates result/body data and sends `self.body`
        to the backend via `self.conn.insertion(self.body)` (persists model topology,
        architecture JSON and weights as lists).

        Raises
        ------
        Exception
            If the model is not compiled or required components (input/layers) are missing,
            Keras will raise an error during `.fit()`.

        Examples
        --------
        >>> ml.add_callback("loss", patience=10)
        >>> ml.fit(x_train, y_train, epochs=100, batch_size=32, validation_split=0.2)
        """
        
        tracemalloc.start()
        self.batch_size = batch_size
        self.history = self.model.fit(
            x=x,
            y=y,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[self.callback],
            validation_split=validation_split,
        )
        self.peak_memory = str(
            si_format(tracemalloc.get_traced_memory()[1], precision=2)
        )

        if not genetic_learning:
            # inclui hyperparametros de treinamento
            self.results = {
                "batchs": batch_size,
                "number_epochs": epochs,
                "patience": self.patience,
                "outputs": self.history.history,
                "accuracy_parameters": None,
            }

            self.body = {
                "task_name": self.task_name,
                "topology_name" : self.topology_name,
                "key_words": [], #think on doing a link with the categories from the platform
                "task_meta_features": self.task_meta_features,
                "macrocontext": self.macrocontext,
                "results": self.results,
                "topology_informations": self.topology_metadata,
                "topology": {
                    "architecture": self.model.to_json(),  # mudar nome para arquitetura
                    "weights": [peso.tolist() for peso in self.model.get_weights()],
                },
            }

            self.topology_id = self.conn.insertion(self.body)["topology_id"] #should actualize the topology id when inserted!

    def fit_transformer(self,x,y,epochs,genetic_learning=False):
        self.batch_size = None
        tracemalloc.start()
        self.history = self.model.train(
            x=x,
            y=y,
            epochs=epochs
        )
        self.peak_memory = str(
            si_format(tracemalloc.get_traced_memory()[1], precision=2)
        )
        if not genetic_learning:
            # inclui hyperparametros de treinamento
            self.results = {
                "batchs": self.batch_size,
                "number_epochs": epochs,
                "patience": self.patience,
                "outputs": self.history,
                "accuracy_parameters": None,
            }

            self.body = {
                "task_name": self.task_name,
                "topology_name" : self.topology_name,
                "key_words": [],
                "task_meta_features": self.task_meta_features,
                "macrocontext": self.macrocontext,
                "results": self.results,
                "topology_informations": self.topology_metadata,
                "topology": {
                    #*** verificar como adicionar as informacoes do modelo com testes
                    "architecture": None,#self.model.to_json(),  # mudar nome para arquitetura
                    "weights": None #[peso.tolist() for peso in self.model.get_weights()],
                },
            }

            self.conn.insertion(self.body)
        next

    def fit_robust_rnn(self,erro_min, X, Y, from_x = True,genetic_learning=False):
        self.batch_size = None
        tracemalloc.start()
        self.history = self.model.train(
            erro_min = erro_min, 
            X = X, 
            Y = Y, 
            from_x = from_x
        )
        self.peak_memory = str(
            si_format(tracemalloc.get_traced_memory()[1], precision=2)
        )
        if not genetic_learning:
            # inclui hyperparametros de treinamento
            self.results = {
                "batchs": self.batch_size,
                "erro_min": erro_min,
                "outputs": self.history,
                "accuracy_parameters": None, #pode adicionar para a classificacao
            }

            self.body = {
                "task_name": self.task_name,
                "topology_name" : self.topology_name,
                "key_words": [],
                "task_meta_features": self.task_meta_features,
                "macrocontext": self.macrocontext,
                "results": self.results,
                "topology_informations": self.topology_metadata,
                "topology": {
                    "architecture": self.hyperparemeters,
                    "weights": {
                        'V' : self.model.V,
                        'V0' : self.model.V0,
                        'W' : self.model.W,
                        'W0' : self.model.W0,
                        'A' : self.model.A,
                        'B' : self.model.B
                    }
                },
            }

            self.conn.insertion(self.body)
        next
    
    def fit_robust_classifier(self,erro_min, X, Y, classes, from_x = True,genetic_learning=False):
        self.batch_size = None
        tracemalloc.start()
        #concertar detalhes abaixo
        self.history = self.model.train(
            erro_min = erro_min, 
            X = X, 
            Y = Y,
            classe=classes,
            from_x = from_x
        )
        self.peak_memory = str(
            si_format(tracemalloc.get_traced_memory()[1], precision=2)
        )
        if not genetic_learning:
            # inclui hyperparametros de treinamento
            self.results = {
                "batchs": self.batch_size,
                "erro_min": erro_min,
                "outputs": self.history,
                "accuracy_parameters": None, #pode adicionar para a classificacao
            }

            weights_all = []
            for i in range(0,len(self.model.classifiers)):
                weights_all.append({
                    "weights": {
                        'V' : self.model.classifiers[i].V,
                        'V0' : self.model.classifiers[i].V0,
                        'W' : self.model.classifiers[i].W,
                        'W0' : self.model.classifiers[i].W0,
                        'A' : self.model.classifiers[i].A,
                        'B' : self.model.classifiers[i].B
                    }
                })

            self.body = {
                "task_name": self.task_name,
                "topology_name" : self.topology_name,
                "key_words": [],
                "task_meta_features": self.task_meta_features,
                "macrocontext": self.macrocontext,
                "results": self.results,
                "topology_informations": self.topology_metadata,
                "topology": {
                    "architecture": self.hyperparemeters,
                    "weights": {
                        'V' : self.model.V,
                        'V0' : self.model.V0,
                        'W' : self.model.W,
                        'W0' : self.model.W0,
                        'A' : self.model.A,
                        'B' : self.model.B
                    }
                },
            }

            self.conn.insertion(self.body)
        next

    def predict(self,input):
        start_time = time.time()
        result = self.model.predict(input)
        end_time = time.time()
        time_spent = (end_time - start_time) * 1000 #time in miliseconds
        return result,time_spent/input.shape[0] #sent it to the back-end to fill the results...
    
    #essa parte poderia receber talvez uma parte especifica, como para redes densas por exemplo
    #porem seria necessaria uma refatoracao
    def replace_intermediate_layer(self, model, layer_id, new_layer):

        layers = [l for l in model.layers]

        x = layers[0].output
        for i in range(1, len(layers)):
            if i == layer_id:
                x = new_layer(x)
            else:
                config = layers[i].get_config()
                cloned_layer = type(layers[i]).from_config(config)
                x = cloned_layer(x)

        new_model = Model(inputs=self.input, outputs=x)
        return new_model

    def insert_intermediate_layer(self, model, layer_id, new_layer):

        layers = [l for l in model.layers]

        x = layers[0].output
        for i in range(1, len(layers)):
            if i == layer_id:
                x = new_layer(x)
            config = layers[i].get_config()
            cloned_layer = type(layers[i]).from_config(config)
            x = cloned_layer(x)

        new_model = Model(inputs=self.input, outputs=x)
        return new_model

    def remove_intermediate_layer(self, model, layer_id):

        layers = [l for l in model.layers]

        x = layers[0].output
        for i in range(1, len(layers)):
            if i == layer_id:
                continue
            else:
                config = layers[i].get_config()
                cloned_layer = type(layers[i]).from_config(config)
                x = cloned_layer(x)

        new_model = Model(inputs=self.input, outputs=x)
        return new_model

    def genetic_start(
        self,
        model_name,
        short_theme,
        input_shape,
        output_shape,
        datax,
        datay,
        validation_split,
        batch_size,
        epochs,
        max_neurons,
        loss,
        optimizer,
        metrics,
        number_of_generations,
        monitor,
        patience,
        activation="relu",
        model=None,
        loss_value=None,
        last_gen=None,
        submit_validation = False
    ):
        self.short_theme = short_theme
        self.add_callback(monitor, patience)
        self.old_generation_model = None
        # self.last_loss_value = None
        self.loss = loss
        self.epochs = epochs
        if model:
            for layer in model.layers:
                layer._name = layer.name + str("_2")
            ngeneration = last_gen
            self.model = model
            self.loss_value = loss_value
            self.input = model.input
            print("\n\n Modelo carregado com sucesso!", end="\n\n")
        else:
            ngeneration = 0
            self.loss_value = inf
            self.add_input(input_shape)
            self.add_dense(1, activation=activation)
            self.add_dense(output_shape)
            self.model = Model(inputs=self.input, outputs=self.stacked_layers)
            print(
                "\n\n There is no loaded model. starting a new model...", end="\n\n"
            )

        while ngeneration < number_of_generations:
            self.old_generation_model = self.model
            if random.randint(1, 20) > 10:
                nlayers = len(self.model.layers)
                layer = Dense(random.randint(1, max_neurons), activation=activation)
                self.model = self.insert_intermediate_layer(
                    self.model, random.randint(1, nlayers - 2), layer
                )

            if random.randint(1, 20) > 10 and len(self.model.layers) > 3:
                nlayers = len(self.model.layers)
                self.model = self.remove_intermediate_layer(
                    self.model, random.randint(1, nlayers - 2)
                )

            layer = Dense(random.randint(1, max_neurons), activation=activation)
            self.model = self.replace_intermediate_layer(
                self.model, random.randint(1, len(self.model.layers) - 2), layer
            )

            self.compile(
                loss,
                optimizer,
                metrics,
                model_name + str(ngeneration),
                generation=ngeneration,
                genetic_learning=True,
            )
            self.fit(
                datax,
                datay,
                self.epochs,
                batch_size,
                validation_split,
                genetic_learning=True,
            )
            loss_valueG = self.history.history["val_loss"][-1]
            self.epochs_used = len(self.history.history["loss"])

            if loss_valueG < self.loss_value:
                self.old_generation_model = self.model
                self.loss_value = loss_valueG
                ngeneration = ngeneration + 1
                current_gen_str = "gen" + str(ngeneration)

                # genetic_name = (
                #     "maxn"
                #     + str(max_neurons)
                #     + "_pat"
                #     + str(self.patience)
                #     + "_loss"
                #     + f.short_loss_name(self.loss)
                # )

                # file_name = f.make_file_name(
                #     self.batch_size,
                #     self.patience,
                #     self.epochs_used,
                #     self.loss,
                #     isgen=True,
                #     current_gen=ngeneration,
                # )

                # extra_dirs = [genetic_name, current_gen_str, file_name]

                # dir_name = f.make_dir_name(
                #     theme=short_theme,
                #     file_name=file_name,
                #     extra_dirs=extra_dirs,
                # )

                # os.makedirs(dir_name, exist_ok=True)

                # self.save(
                #     dir_name + "/saved_model",
                #     include_optimizer=True,
                # )

                # f.plot_loss(
                #     history=self.history,
                #     batch_size=self.batch_size,
                #     patience=self.patience,
                #     epochs_used=self.epochs_used,
                #     peak_memory=self.peak_memory,
                #     file_name=file_name,
                #     theme=self.short_theme,
                #     loss=self.loss,
                #     isgen=True,
                #     current_gen=ngeneration,
                #     genetic_name=genetic_name,
                #     current_gen_str=current_gen_str,
                # )
                self.results = {
                    "batchs": self.batch_size,
                    "number_epochs": self.epochs,
                    "patience": self.patience,
                    "outputs": self.history.history,
                    "accuracy_parameters": None,
                }

                self.body = {
                    "task_name": self.task_name,
                    "topology_name" : self.topology_name + "_generation_" + str(ngeneration),
                    "key_words": [],
                    "task_meta_features": self.task_meta_features,
                    "macrocontext": self.macrocontext,
                    "results": self.results,
                    "topology_informations": self.topology_metadata,
                    "topology": {
                        "architecture": self.model.to_json(),  # mudar nome para arquitetura
                        "weights": [peso.tolist() for peso in self.model.get_weights()],
                    },
                }
                self.topology_id = self.conn.insertion(self.body)['topology_id']
                
                if submit_validation:
                    if not self.test_input or ngeneration < 2:
                        self.load_test_input(taskname = self.task_name, 
                                       taskid = self.taskid)
                    
                    predictions, time_spent = self.predict(np.array(self.test_input["data"]))
                    self.submit_result(accuracy_parameter = "mean_squared_error", #the own route should search for it...
                         taskname = self.task_name,
                         taskid = self.taskid,
                         topology_id = self.topology_id,
                         results = predictions,
                         execution_time = time_spent)
            else:
                self.model = self.old_generation_model

        next

    # it is necessary to fulfill all the metadata in order to the functions continue to work...
    def import_topology(self,topology_name = None,topology_id = None):
        value_topology = None
        if topology_id:
            value_topology = topology_id
        else:
            value_topology = ""
        if topology_name:
            next
        else:
            topology_name = ""
        data = {
            "id" : value_topology,
            "topology_name" : topology_name
        }
        res = self.conn.import_model(data)
        topology_metadata = res["topology_metadata"]

        self.body = topology_metadata
        self.task_name = topology_metadata["task_name"]
        self.topology_name = topology_metadata["topology_name"]
        self.key_words = topology_metadata["key_words"]
        self.task_meta_features = topology_metadata["task_meta_features"]
        self.macrocontext = topology_metadata["macrocontext"]
        self.results = topology_metadata["results"]
        self.topology_metadata = topology_metadata["topology_informations"]

        topology_kind = res["kind"]
        topology = res["topology"]
        if topology_kind == "model":
            architecture = topology['architecture']
            weights = topology['weights']

            self.model = model_from_json(architecture)
            self.model.set_weights([np.array(w) for w in weights])
            self.imported = True

    #def load_train_data(self, taskname, taskid):
    #    data = {
    #        "taskname" : taskname,
    #        "id" : taskid
    #    }
    #    self.train_data = self.conn.import_train_data(data)
    #    return self.train_data



    def load_train_data(self, taskname, taskid, local_path='./data'):
        # if user provides path, download
        if local_path:
            file_name = f"{taskname}_{taskid}_train_data.json"
            file_path = os.path.join(local_path, file_name)

            # if user has the data (in the right path)
            if os.path.exists(file_path):
                print(f"Loading data from local file: {file_path}")
                with open(file_path, 'r') as file:
                    self.train_data = json.load(file)
            else:
                print("Data not found locally, downloading from API")
                data = {
                    "taskname": taskname,
                    "id": taskid
                }
                self.train_data = self.conn.import_train_data(data)

                with open(file_path, 'w') as file:
                    json.dump(self.train_data, file)
                print(f"Data saved locally in: {file_path}")

        # if user doesnt provides path, just load
        else:
            print("No local path provided, downloading from API")
            data = {
                "taskname": taskname,
                "id": taskid
            }
            self.train_data = self.conn.import_train_data(data)
        
        return self.train_data



    def load_test_input(self, taskname, taskid):
        data = {
            "taskname" : taskname,
            "id" : taskid
        }
        self.test_input = self.conn.import_test_data(data)
        return self.test_input 
       
    #change the function, we just need to send the topology id to the back, this is just for testing before integration
    def submit_result(self,accuracy_parameter,taskname,taskid,topology_id,results,execution_time):
            #maybe can get the topology id from the own self
            result_data = {
                "accuracy_parameter" : accuracy_parameter,
                "taskname" : taskname,
                "taskid": taskid,
                "topology_id": topology_id,
                "results" : {
                    "data" : results.tolist(),
                    "execution_time" : execution_time
                }
            }
            result = self.conn.insert_results(result_data)
            result = result["result"]
            print("your result was : \n" + str(result["accuracy_parameter"]) + " : " + str(result["parameter_result"]))
            return result
        

    def save(self, path, include_optimizer=None):
        """
        Save the Keras model to disk.

        Parameters
        ----------
        path : str
            Path where the model will be saved (Keras `Model.save` behavior).
        include_optimizer : bool, optional
            If True, include optimizer state in the saved model (if supported).
            Default behavior depends on Keras version.

        Returns
        -------
        None

        Examples
        --------
        >>> ml.save("results/heatsense_test/saved_model", include_optimizer=True)
        """
        
        self.model.save(path, include_optimizer=include_optimizer)
        # for valor in valores:
        #     self.metadata.append({"variavel": valor})

    def task():
        return

    # def mk_model(m_type, *args):
    #     model = m_type
    #     for layer in args:
    #         model.add(layer)
    #     return model


# --------------------------------------------------  Criação da Model --------------------------------------------------