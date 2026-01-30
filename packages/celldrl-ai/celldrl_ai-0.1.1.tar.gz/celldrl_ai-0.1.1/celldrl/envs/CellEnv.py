## load packages


import pyreadr
import os
import math
import time
import numpy as np
import pandas as pd
import anndata as ad
import scanpy as sc
import matplotlib.pyplot as plt
import random
import seaborn as sns
import umap
import warnings
import glob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from scipy.special import softmax


## Gym
import gymnasium as gym 
from gym import Env
from gym.spaces import Box
from gym.envs.registration import register

## Baselines
from stable_baselines3 import SAC
import stable_baselines3 as sb3
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

# PyTorch
import torch
import torchvision
from torch import nn
from torch.utils.data import DataLoader

## Baselines
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.vec_env import VecVideoRecorder
from stable_baselines3.common.monitor import Monitor

        
class CellEnv (Env):
    def __init__(self, sf, n_comp, Trajectory_length,scale, n_gen_cells, norm, lammda, theta, total_timesteps,reward_signal,select_by,regularization_type, self_state_loss, max_reward_bound, min_reward_bound,max_trajectory_bound,min_trajectory_bound, seed):
            
        self.sf = sf
        self.n_comp = n_comp
        self.seed = seed
        self.Trajectory_length = Trajectory_length
        self.scale = scale
        self.n_gen_cells = n_gen_cells
        self.norm = norm
        self.lammda = lammda
        self.theta =  theta
        self.total_timesteps = total_timesteps
        self.reward_signal = reward_signal
        self.select_by = select_by
        self.regularization_type = regularization_type
        self.self_state_loss = self_state_loss
        self.max_reward_bound =max_reward_bound
        self.min_reward_bound = min_reward_bound
        self.max_trajectory_bound = max_trajectory_bound
        self.min_trajectory_bound = min_trajectory_bound
        
        # Actions Space
        self.action_space = Box(np.array([-scale, 0.01, 0]), 
                                np.array([scale, scale, scale]), 
                                dtype=np.float32)

        # Observation Space
        self.observation_space = Box(low=-np.inf, 
                                     high=np.inf, 
                                     shape=(1,), 
                                     dtype=np.float64)
        # Define initial state and other environment-specific variables

        self.min_max_bound = self.max_reward_bound - self.min_reward_bound
        self.csl_distances = list(reversed(np.arange(0,self.min_max_bound, self.min_max_bound/Trajectory_length)))
        self.csl_distances.insert(0, float(self.self_state_loss[0]))
        self.sf_sm = softmax(np.median(sf.X, axis=0))
        
        # Create a list as a class attribute
        self.regularization_list = []
        self.KL_losses = []
        self.mu_gen_list = []
        self.sigma_gen_list = []
        self.self_state_loss_list = []
        self.KL_losses = []
        self.mu_gen_list = []
        self.sigma_gen_list = []
        self.s_scaler_list = []
        self.self_state_loss_list = []
        self.mu_pert_list = []
        self.sigma_pert_list = []
        self.gen_adatas = []
        

            
    def reset(self):
        # Reset Trajectory observation space
        self.state = np.array([random.uniform(0,0.05)]).astype(float)
        # Reset Trajectory time
        self.Trajectory_length = Trajectory_length
        return self.state 

    def step(self, action):
        mu_gen, sigma_gen, s_scaler = action[0], abs(action[1]), action[2]
        
        gen_adata = celldrl.actions_training (adata = adata,
                                               concate_states = concate_states, 
                                               svd_u_matrix = svd_u_matrix, 
                                               s = s,
                                               s_scaler = s_scaler,
                                               states_mu = states_mu,
                                               n_comp =n_comp, 
                                               n_gen_cells = n_gen_cells, 
                                               mu_gen = mu_gen, 
                                               sigma_gen = sigma_gen, 
                                               select_by = select_by,
                                               norm = norm)      

        gen_adata.obs[select_by] = "Generated"            

        ## Calculate KLD and Cosine Similarity:
        gen_sm = softmax(np.median(gen_adata.X, axis=0))        
        
        kl_loss = celldrl.kl_divergence(gen_sm, self.sf_sm)
        cs_pq_mga = cosine_similarity(np.array([gen_sm]), np.array([self.sf_sm]))
        
        if regularization_type == 'entropy':
            entropy_rg = celldrl.entropy_regularization(gen_sm)
            regularization = lammda * entropy_rg
        elif regularization_type == 'l1':
            regularization = lammda * sum(abs(gen_sm))
        elif regularization_type == 'l2':
            regularization = lammda * sum(pow(gen_sm, 2))
        elif regularization_type == 'None':
            regularization = 0
            
        # print(regularization)
        cellular_state_loss =  (1- cs_pq_mga) * theta * kl_loss + regularization
        
        ## Update Self State by the current observations
        
        self.state = cellular_state_loss.flatten()     

        ## Collect lists
        self.KL_losses.append(kl_loss) 
        self.mu_gen_list.append(mu_gen)
        self.sigma_gen_list.append(sigma_gen)
        self.s_scaler_list.append(s_scaler)
        self.regularization_list.append(regularization)
        self.self_state_loss_list.append(cellular_state_loss)
        self.gen_adatas.append(gen_adata)
        ## Delete gen_adata
        del gen_adata
        
        # Reduce Trajectory length by 1 step
        self.Trajectory_length -= 1 
        
        # Calculate reward
        if self.state >= self.min_reward_bound and self.state <=self.max_reward_bound: 

            reward = float (reward_signal + (1-self.state))
        else: 
            reward = float(-1) 
            
        # Check if Trajectory is done 
        if self.state >=self.max_trajectory_bound:
            done = True
        elif self.state <=self.min_trajectory_bound: 
            done = True   
        elif self.Trajectory_length <= 0: 
            done = True
        else:
            done = False
        info = {}
        
        # Return step information
        return self.state, reward, done, info
    
    def render(self):
        pass