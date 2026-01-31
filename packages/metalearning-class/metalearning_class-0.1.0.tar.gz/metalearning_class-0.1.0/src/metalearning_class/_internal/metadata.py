#-modificar as informacoes, pois tudo deveria ser em ingles...
#-criar um tipo de estrutura para testar generalizacao de modelos entre multiplas tarefas
#-criar inumeras funcoes de avaliacao e validacao por etapas de hyperparametros, que devem ser usadas para 
#aprender a aprender

import inspect
import numpy as np

topology_metadata = {
    "Tipo": "DNN",
    "geracao": 0,  # aplicar aprendizado genetico
    "versao": 1,
    "loss_function": "mean_squared_error",
    "optimizer": "adam",
    "nome": "preditor-espectro-de-frequencia-meta-materiais",
    "hyperparameters": {"camadas": [200, 200, 301], "numero_camadas": 3},
}

task_meta_features = {
    "Tipo": "sequences",
    "Descricao" : "preditor-espectro-de-frequencia-meta-materiais a partir de deep learning",
    "Dimensoes_Entrada": (4),
    "Dimensoes_Saida": (301),
    "Dados": {"link_github": " https://github.com/SensongAn/Meta-atoms-data-sharing"},
    "Parametros_de_acuracia": ["corr_pearson_media_entre_frequencias"],
}

resultados = {
    "batchs": 32,
    "numero_epocas": 1000,
    "paciencia": 3,
    "outputs": {"loss train": [], "loss test": []},
    "parametros_de_acuracia": {"corr_pearson_media_entre_frequencias": "None"},
}

task_name = "simulacaocoeficientedetransimissaomateriaiscilindricos"

# task_name,task_meta_features,topology_informations,topology
body = {
    "task_name": task_name,
    "palavras_chave": [],
    "task_meta_features": task_meta_features,
    "contexto": "simulacoes_de_meta_superficies_por_dnn",
    "resultados": resultados,
    "topology_informations": topology_metadata,
    "topology": "modelD.to_json()",
}

#definicao de topologias para hyperparametros isolados, estes poderiam ser encaixados por exemplo
# em topology_metadata de alguma forma que devera ser pensada a medida que o codigo eh construido

#possivel conceito de capturar informacoes apenas cruciais para economizar espaco, com a capacidade de reconstrucao
#mantida
hyperparameter_function_learning = {
                        "user" : "acgabriel",
                        "access" : "restrict", #como bloquear o acesso a determinadas caracteristicas do banco de dados...
                        "hyperparameter_name" : "mimificacao",
                        "shape": [4,10],
                        "hyperparameter_data": np.zeros((4,10)),
                        "function" : inspect.getsource("code"),
                        "function-name": "mimifica2",
                        "data": np.random(1,100,10),
                        "test_parameters": "numero_de_ativacoes",
                        "result_parameter": 0.5,
                        "testname": "ativacao_neuronios",
                        "testeid" : 1,
                        "kind_of_analysis" : "teste_arvore_invertida",
                        "linked_model" : "v2_model", #pode linkar depois 
                        "compatibility" : "v2"
                        }