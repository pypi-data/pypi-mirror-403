# IMPORTANTE: SEPARAR em = pasta transformer, e dois arquivos "base" e "utils"



from metalearning_class.modules.transformer_utils import Transformer
from metalearning_class.modules.transformer_utils import CustomSchedule
from metalearning_class.modules.transformer_utils import create_padding_mask
from metalearning_class.modules.transformer_utils import create_look_ahead_mask
import tensorflow as tf
import time
import numpy as np
import pandas as pd
import random as rd

#-------------------------------------- Definicao do modelo

'''

Modelo do tipo final, isto indica que ele nao esta inserido na possibilidade de novas composicoes de modelos no momento
isto deveria ser feito dentro da propria classe de meta-learning ao que esta sendo avaliado: Ela encapsula possiveis blocos
para montar um modelo maior e complexo. 

'''
class Transformer_gerenciator():
    
    def __init__(self,num_layers,d_model,num_heads,dff,pe_input,pe_target,words,input_vocab_size,target_vocab_size,task_meta_features=None,hyperparameters = None):
        self.d_model = d_model
        self.words = words
        if task_meta_features:
            task_meta_features["Input_dimensions"] = pe_input        
            task_meta_features["Output_dimensions"] = pe_target
            hyperparameters = {
                'hyperparameters': {
                    'num_layers' : num_layers,
                    'd_model' : d_model,
                    'num_heads' : num_heads,
                    'dff' : dff, #precisa nomear melhor
                    'pe_input' : pe_input,
                    'pe_target' : pe_target,
                    'words' : words,
                    'input_vocab_size' : input_vocab_size,
                    'target_vocab_size' : target_vocab_size
                }
            }
        self.transformer = Transformer(
            num_layers = num_layers, 
            d_model = d_model, 
            num_heads = num_heads, 
            dff = dff,
            pe_input=pe_input, 
            pe_target=pe_target,
            words = words,
            input_vocab_size= input_vocab_size,
            target_vocab_size = target_vocab_size #parece indicar tambem o tamanho da saida
        )
    
        self.learning_rate = CustomSchedule(self.d_model)
    
        self.optimizer = tf.keras.optimizers.Adam(self.learning_rate, beta_1=0.9, beta_2=0.98, epsilon=1e-9)
        self.loss_object = tf.keras.losses.MeanAbsoluteError()
        self.train_loss = tf.keras.metrics.Mean(name='train_loss')
    
    def compile(self,loss_object = None, optimizer = None, metrics = None):

        if optimizer:
            self.optimizer = optimizer
        else:
            self.optimizer = tf.keras.optimizers.Adam(self.learning_rate, beta_1=0.9, beta_2=0.98, epsilon=1e-9)
        if loss_object:
            self.loss_object = loss_object
        else:
            self.loss_object = tf.keras.losses.MeanAbsoluteError()
        if metrics:
            self.train_loss = metrics
        else:
            self.train_loss = tf.keras.metrics.Mean(name='train_loss')
    
    
    def loss_function(self,real, pred):
        mask = tf.math.logical_not(tf.math.equal(real, 0))
        loss_ = self.loss_object(real, pred)
    
        mask = tf.cast(mask, dtype=loss_.dtype)
        loss_ *= mask
    
        return tf.reduce_sum(loss_)/tf.reduce_sum(mask)
    
    
    
    def create_masks(self,inp, tar):
        enc_padding_mask = create_padding_mask(inp)
        dec_padding_mask = create_padding_mask(inp)
    
        look_ahead_mask = create_look_ahead_mask(tf.shape(tar)[1])
        dec_target_padding_mask = create_padding_mask(tar)
        combined_mask = tf.maximum(dec_target_padding_mask, look_ahead_mask)
      
        return enc_padding_mask, combined_mask, dec_padding_mask
    
    def save(self):
        checkpoint_path = "checkpoints"
    
        ckpt = tf.train.Checkpoint(transformer=self.transformer, optimizer=self.optimizer)
    
        ckpt_manager = tf.train.CheckpointManager(ckpt, checkpoint_path, max_to_keep=5)
    
        if ckpt_manager.latest_checkpoint:
            ckpt.restore(ckpt_manager.latest_checkpoint)
            print ('Latest checkpoint restored!!')
    
    @tf.function
    def train_step(self,inp, tar):
        #a contrucao abaixo parece ser devido ao formato para word, verificar
        #tar_inp = tar[:, :-1]
        #tar_real = tar[:, 1:]
        
        #atualmente modificado para funcionar apenas com o proprio dado
        #na pratica o decoder recebe uma ajuda da entrada com relacao a cada dado
        #como resultado, isto devido ao tipo de dado que temos
        #enc_padding_mask, combined_mask, dec_padding_mask = create_masks(inp, inp)
        
        #solucao temporaria:
        enc_padding_mask, combined_mask, dec_padding_mask = self.create_masks(inp[0], inp[0])
        
        
        with tf.GradientTape() as tape:
            predictions, _ = self.transformer(
                inp, inp, 
                True, 
                enc_padding_mask, 
                combined_mask, 
                dec_padding_mask
            )
            loss = self.loss_function(tar, predictions)
    
        gradients = tape.gradient(loss, self.transformer.trainable_variables)    
        self.optimizer.apply_gradients(zip(gradients, self.transformer.trainable_variables))
    
        self.train_loss(loss)
    
    
    def train_words(self,dataset,EPOCHS):
        
        if not self.words:
            exception = "trying to use transformers to words data without correct flag. Try define words = True"
            raise Exception(exception)
        
        results_loss = []
        for epoch in range(EPOCHS):
            start = time.time()
        
            self.train_loss.reset_states()
          
            for (batch, (inp, tar)) in enumerate(dataset): 
                self.train_step(inp, tar)
                # 55k samples
                # we display 3 batch results -- 0th, middle and last one (approx)
                # 55k / 64 ~ 858; 858 / 2 = 429
                if batch % 64 == 0:
                    print ('Epoch {} Batch {} Loss {:.4f}'.format(epoch + 1, batch, self.train_loss.result()))
            results_loss.append(self.train_loss.result())
                
            #if (epoch + 1) % 5 == 0:
            #    ckpt_save_path = ckpt_manager.save()
            #    print ('Saving checkpoint for epoch {} at {}'.format(epoch+1, ckpt_save_path))
            
            print ('Epoch {} Loss {:.4f}'.format(epoch + 1, self.train_loss.result()))
        
            print ('Time taken for 1 epoch: {} secs\n'.format(time.time() - start))
        
        return results_loss
    
    def train(self,x,y,epochs):
        results_loss = []
        frobenius_variation = []
        for epoch in range(epochs):
            
            indexs = list(range(0,len(x))) 
            rd.shuffle(indexs)
            x = x[np.array(indexs)]
            y = y[np.array(indexs)]
            
            start = time.time()
            self.train_loss.reset_states()
            
            for i in range(0,len(x)):
                self.train_step(x[i],y[i])
                # 55k samples
                # we display 3 batch results -- 0th, middle and last one (approx)
                # 55k / 64 ~ 858; 858 / 2 = 429
                if i % 64 == 0:
                    print ('Epoch {} Batch {} Loss {:.4f}'.format(epoch + 1, i, self.train_loss.result()))
            results_loss.append(float(self.train_loss.result()))
            weights = np.array(self.transformer.final_layer.get_weights()[0])
            frobenius_variation.append(np.linalg.norm(weights, 'fro'))
           # if (epoch + 1) % 5 == 0:
           #     ckpt_save_path = ckpt_manager.save()
           #     print ('Saving checkpoint for epoch {} at {}'.format(epoch+1, ckpt_save_path))
            
            print ('Epoch {} Loss {:.4f}'.format(epoch + 1, self.train_loss.result()))

            print ('Time taken for 1 epoch: {} secs\n'.format(time.time() - start))
        return [results_loss,weights]
    
    def evaluate_step(self,inp):
        #a contrucao abaixo parece ser devido ao formato para word, verificar
        #tar_inp = tar[:, :-1]
        #tar_real = tar[:, 1:]
    
        enc_padding_mask, combined_mask, dec_padding_mask = self.create_masks(inp[0], inp[0])
    
        predictions, _ = self.transformer(
            inp, inp, 
            False, 
            enc_padding_mask, 
            combined_mask, 
            dec_padding_mask
        )
        return predictions[: ,-1:, :]   

