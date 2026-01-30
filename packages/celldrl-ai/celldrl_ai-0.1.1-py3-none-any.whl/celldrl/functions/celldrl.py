

## loading packages

print ("Loading Packages ...")

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
from scipy.sparse.linalg import svds
from sklearn import preprocessing

## Gym

import gymnasium as gym
from gymnasium import Env
from gymnasium.spaces import Box
from gymnasium.envs.registration import register

# # PyTorch
# import torch
# import torchvision
# from torch import nn
# from torch.utils.data import DataLoader

## Baselines
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.vec_env import VecVideoRecorder
from stable_baselines3.common.monitor import Monitor

## Params

## Key Functions:

## Pre- Procecessing:

def pp_sc_object (adata, min_counts, min_genes, min_cells, n_HVGs, max_scale_value):
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_cells(adata, min_counts = min_counts)

    sc.pp.filter_genes(adata, min_cells=min_cells)
    sc.pp.normalize_per_cell(adata, counts_per_cell_after=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=n_HVGs,
        subset=True, flavor="seurat_v3")
    sc.pp.scale(adata, max_value=max_scale_value)
#     adata.X = adata.X.astype('float64')

    return adata

## Dim Reduction (PCA and UMAP):

def dim_reduction (adata, n_neighbors, n_pcs, min_dist):
    sc.tl.pca(adata)
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)
    sc.tl.umap(adata, min_dist=min_dist)
    return adata

## Select cellular states based on user defined groups:

def select_cellular_states (adata, select_by, Intial_State, Terminal_State):
    Si , St = adata[adata.obs[select_by] == Intial_State].copy(), adata[adata.obs[select_by] == Terminal_State].copy()
    concate_states = ad.concat([Si , St], join="inner").copy()
    return Si , St, concate_states

def cellular_states_mcu (concate_states, n_comp):
    states_mu = np.array([concate_states.X.mean(0)])
    concate_states_df =concate_states.to_df(layer=None)
    cov_matrix = pd.DataFrame(np.cov(concate_states_df.T))
    # u, s, vh = np.linalg.svd(cov_matrix)
    u, s, vh = svds(cov_matrix.to_numpy(), k=n_comp, solver='arpack')
    del vh
    cov_adata = ad.AnnData(cov_matrix)
    svd_u_matrix = pd.DataFrame(u)
    return states_mu, cov_matrix, svd_u_matrix, s

def calculate_log(value):
    if value <= 0:
        print("Error: Input must be a positive number.")
        return None
    else:
        result = math.log2(abs(value))
        return result

def actions_prediction (adata, concate_states, svd_u_matrix, s, s_scaler, states_mu,
                n_comp, mu_gen, sigma_gen, n_gen_cells, select_by, norm):

    ## Select the number of components:
    svd_u_matrix = pd.DataFrame(svd_u_matrix)
    u_n_comp = svd_u_matrix.iloc[:, 0:n_comp].copy()

    ## X sampling from independant Gaussian distribution:
    X = np.random.normal(loc=mu_gen,
                         scale=sigma_gen,
                         size=(n_gen_cells, n_comp)).copy()
    ## Data genration after taking an action:
    scaled_s = np.sqrt(s_scaler + s[0:n_comp])
    eigenvectors = np.matmul(u_n_comp, np.diag(scaled_s))
    norm_mu = preprocessing.normalize(states_mu, norm =norm)
    generated_data = np.matmul(X, eigenvectors.T) + norm_mu

    ## Prepare anndata objects:
    gen_adata = ad.AnnData(generated_data)
    gen_adata.var_names = concate_states.var_names
    gen_adata.obs["Data_Source"] = "Generated"
    gen_adata.obs[select_by] = "Generated"



    ## Add metadata and concate
    adata.obs["Data_Source"] = "Real"
    real_gen_adata = ad.concat([gen_adata, adata]).copy()
    concate_gen_adata = ad.concat([gen_adata, concate_states]).copy()

    return gen_adata, real_gen_adata, concate_gen_adata

def actions_training (adata, concate_states, svd_u_matrix, s, s_scaler, states_mu,
                n_comp, mu_gen, sigma_gen, n_gen_cells, select_by, norm):

    ## Select the number of components:
    svd_u_matrix = pd.DataFrame(svd_u_matrix)
    u_n_comp = svd_u_matrix.iloc[:, 0:n_comp].copy()

    ## X sampling from independant Gaussian distribution:
    X = np.random.normal(loc=mu_gen,
                         scale=sigma_gen,
                         size=(n_gen_cells, n_comp)).copy()
    ## Data genration after taking an action:
    scaled_s = np.sqrt(s_scaler + s[0:n_comp])
    eigenvectors = np.matmul(u_n_comp, np.diag(scaled_s))
    norm_mu = preprocessing.normalize(states_mu, norm =norm)
    generated_data = np.matmul(X, eigenvectors.T) + norm_mu

    ## Prepare anndata objects:
    gen_adata = ad.AnnData(generated_data)
    gen_adata.var_names = concate_states.var_names
    gen_adata.obs["Data_Source"] = "Generated"
    gen_adata.obs[select_by] = "Generated"

    return gen_adata


def kl_divergence(p, q):
    kl = 0.0
    for i in range(len(p)):
        if p[i] is None or q[i] is None:
            continue
        if p[i] == 0.0:
            continue
        kl += p[i] * calculate_log(p[i]/q[i])
        # kl = sum(p[i] * calculate_log(p[i]/q[i]) for i in range(len(p)))
    return kl

# calculate the cellular state loss

def cellular_state_loss (adata, sf, select_by, theta):

    names = []
    kl_pq_list = []
    cs_pq_mga_list = []
    cs_pq_pca_list = []
    cs_distance_both_list = []

    timepoints = np.array(adata.obs[select_by].unique())

    for x in timepoints:
        names.append(x)
        si = adata[adata.obs[select_by] == x]
        si_sm = softmax(si.X.mean(0), axis=0)
        sf_sm = softmax(sf.X.mean(0), axis=0)

        ## Prop
        # si_prop = si_sm/ si_sm.sum(axis=0, keepdims=True)
        # sf_prop = sf_sm/ sf_sm.sum(axis=0, keepdims=True)

        kl_pq = kl_divergence(si_sm, sf_sm)
        kl_pq_list.append(kl_pq)

        ## CS on  MGA space
#         cs_pq_mga = cosine_similarity(np.array([si.X.mean(0)]), np.array([sf.X.mean(0)])) * kl_pq
#         cs_pq_mga = cosine_similarity(np.array([si_sm]), np.array([sf_sm])) * kl_pq
        cs_pq_mga = (1- cosine_similarity(np.array([si_sm]), np.array([sf_sm]))) * kl_pq * theta

        cs_pq_mga_list.append(cs_pq_mga)


        ## Calculate centroids for the first two PCs
        si_pcs = pd.DataFrame(si.obsm['X_pca']).iloc[:, 0:2]
        si_pcs_c = KMeans(n_clusters=1).fit(si_pcs).cluster_centers_
        sf_pcs = pd.DataFrame(sf.obsm['X_pca']).iloc[:, 0:2]
        sf_pcs_c = KMeans(n_clusters=1).fit(sf_pcs).cluster_centers_

        ## CS on PCA space
#         cs_pq_pca = cosine_similarity(si_pcs_c, sf_pcs_c) * kl_pq
        cs_pq_pca = (1- cosine_similarity(si_pcs_c, sf_pcs_c)) * kl_pq

        cs_pq_pca_list.append(cs_pq_pca)

        cs_distance_both = np.mean([cs_pq_mga ,cs_pq_pca])
        cs_distance_both_list.append(cs_distance_both)

    cs_pq_mga_list = np.reshape(np.vstack(cs_pq_mga_list), -1)
    cs_pq_pca_list = np.reshape(np.vstack(cs_pq_pca_list), -1)

    df_res = pd.DataFrame(np.vstack((names,kl_pq_list, cs_pq_mga_list, cs_pq_pca_list, cs_distance_both_list))).T
    # df_res.set_index(0)
    df_res[1]=df_res[1].astype(float)
    df_res[2]=df_res[2].astype(float)
    df_res[3]=df_res[3].astype(float)
    df_res[4]=df_res[4].astype(float)
    df_res = df_res.set_axis(['X', 'KLD', "CS_MGA", "CS_PCA", "CS_Both"], axis=1)
    csl_res = df_res.sort_values(by=['KLD'], ascending=False)
    return csl_res

def learning_bounds_scores (si, sf, alpha, beta, gamma, min_trajectory_bound, theta):
    si_sm = softmax(si.X.mean(0), axis=0)
    sf_sm = softmax(sf.X.mean(0), axis=0)
    kl_pq = kl_divergence(si_sm, sf_sm)
    ## CS on  MGA space
    two_state_loss = (1- cosine_similarity(np.array([si_sm]), np.array([sf_sm]))) * kl_pq * theta
    min_reward_bound = two_state_loss * alpha
    max_reward_bound = two_state_loss * beta
    max_trajectory_bound = two_state_loss * gamma

    

    min_reward_bound = min_reward_bound.item()
    max_reward_bound = max_reward_bound.item()
    
    min_trajectory_bound = min_trajectory_bound
    max_trajectory_bound = max_trajectory_bound.item()
    return two_state_loss, min_reward_bound, max_reward_bound, max_trajectory_bound, min_trajectory_bound

# Plot learning_bounds_scores

def plot_lbs (csl_res,
              select_by,
              self_state_loss,
              min_reward_bound,
              max_reward_bound,
              max_trajectory_bound,
              min_trajectory_bound):

    ax = csl_res.plot.barh(x = 'X', rot=0)
    plt.axvline(x=max_trajectory_bound,linewidth=2, color='red', linestyle='--')
#     plt.axvline(x=-1*max_trajectory_bound,linewidth=2, color='red', linestyle='--')
    plt.axvline(x=min_trajectory_bound,linewidth=1, color='red', linestyle='--')
#     plt.axvline(x=min_trajectory_bound*-1,linewidth=1, color='red', linestyle='--')
    plt.axvline(x=max_reward_bound,linewidth=1, color='black', linestyle='--')
    plt.axvline(x=self_state_loss,linewidth=1, color='green')
    plt.axvline(x=min_reward_bound,linewidth=1, color='black', linestyle='--')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=1)
    plt.axvspan(min_reward_bound,max_reward_bound, color='green', alpha=0.1)
    plt.axvspan(max_reward_bound,max_trajectory_bound, color='red', alpha=0.05)
    plt.axvspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
    plt.axvspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
    plt.axvspan(0,min_trajectory_bound, color='red', alpha=0.3)
    plt.axvspan(max_trajectory_bound,max_trajectory_bound+0.05, color='red', alpha=0.3)
    plt.ylabel(select_by, fontsize=10)

# def plot_actions_losses (self_state_loss_list,KL_losses,mu_gen_list, sigma_gen_list, s_scaler_list,
#               file_name, dirctory):
#     csl = np.reshape(np.vstack(self_state_loss_list), -1)
#     df_res = pd.DataFrame(np.vstack((KL_losses,mu_gen_list, sigma_gen_list, csl, s_scaler_list))).T
#     # df_res.set_index(0)
#     df_res[0]=df_res[0].astype(float)
#     df_res[1]=df_res[1].astype(float)
#     df_res[2]=df_res[2].astype(float)
#     df_res[3]=df_res[3].astype(float)
#     df_res[4]=df_res[4].astype(float)

#     actions_losses = df_res.set_axis(['KLD', "Action_Mu", "Action_Sigma", "Cellular State Loss", "Eigenvalues_Scaler",], axis=1, inplace=False)
#     actions_losses.index.name = 'Time Steps'
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Action_Mu", palette = "Set2")
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Action_Sigma", palette = "Set2")
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Eigenvalues_Scaler", palette = "Set2")

#     face_grid.legend(labels=['Action_Mu','Action_Sigma', "Eigenvalues_Scaler"])
#     plt.ylabel("Model Training - Actions Space", fontsize=10)
#     fig = face_grid.figure
#     ax = fig.gca()
#     os.chdir(dirctory)
#     face_grid.figure.savefig((file_name +".pdf"))
#     return actions_losses


# def plot_actions_losses (self_state_loss_list,KL_losses,mu_gen_list, sigma_gen_list, s_scaler_list):
#     csl = np.reshape(np.vstack(self_state_loss_list), -1)
#     df_res = pd.DataFrame(np.vstack((KL_losses,mu_gen_list, sigma_gen_list, csl, s_scaler_list))).T
#     # df_res.set_index(0)
#     df_res[0]=df_res[0].astype(float)
#     df_res[1]=df_res[1].astype(float)
#     df_res[2]=df_res[2].astype(float)
#     df_res[3]=df_res[3].astype(float)
#     df_res[4]=df_res[4].astype(float)
#
#     actions_losses = df_res.set_axis(['KLD', "Action_Mu", "Action_Sigma", "Cellular State Loss", "Eigenvalues_Scaler",], axis=1, inplace=False)
#     actions_losses.index.name = 'Time Steps'
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Action_Mu", palette = "Set2")
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Action_Sigma", palette = "Set2")
#     face_grid =  sns.lineplot(data=actions_losses, x= 'Time Steps',  y = "Eigenvalues_Scaler", palette = "Set2")
#
#     face_grid.legend(labels=['Action_Mu','Action_Sigma', "Eigenvalues_Scaler"])
#     plt.ylabel("Model Training - Actions Space", fontsize=10)
#     # fig = face_grid.figure
#     # ax = fig.gca()
#     # os.chdir(dirctory)
#     # face_grid.figure.savefig((file_name +".pdf"))
#     return actions_losses
#
# def plot_actions_losses(self_state_loss_list, KL_losses, mu_gen_list, sigma_gen_list, s_scaler_list):
#     csl = np.reshape(np.vstack(self_state_loss_list), -1)
#     df_res = pd.DataFrame(np.vstack((KL_losses, mu_gen_list, sigma_gen_list, csl, s_scaler_list))).T
#     df_res[0] = df_res[0].astype(float)
#     df_res[1] = df_res[1].astype(float)
#     df_res[2] = df_res[2].astype(float)
#     df_res[3] = df_res[3].astype(float)
#     df_res[4] = df_res[4].astype(float)
#
#     actions_losses = df_res.set_axis(['KLD', "Action_Mu", "Action_Sigma", "Cellular State Loss", "Eigenvalues_Scaler"], axis=1, inplace=False)
#     actions_losses.index.name = 'Time Steps'
#
#     # Create a new figure
#     plt.figure()
#
#     # Plot the data
#     face_grid = sns.lineplot(data=actions_losses, x='Time Steps', y="Action_Mu", palette="Set2")
#     sns.lineplot(data=actions_losses, x='Time Steps', y="Action_Sigma", palette="Set2")
#     sns.lineplot(data=actions_losses, x='Time Steps', y="Eigenvalues_Scaler", palette="Set2")
#
#     # Add legend
#     face_grid.legend(labels=['Action_Mu', 'Action_Sigma', "Eigenvalues_Scaler"])
#
#     # Set labels
#     plt.ylabel("Model Training - Actions Space", fontsize=10)
#
#     # Display the plot
#     plt.show()
#
#     print("Done")
#     # Optionally, save the figure
#     # plt.savefig("figure.png")
#
#     return actions_losses


def plot_actions_losses(self_state_loss_list, KL_losses, mu_gen_list, sigma_gen_list, s_scaler_list):
    csl = np.reshape(np.vstack(self_state_loss_list), -1)
    df_res = pd.DataFrame(np.vstack((KL_losses, mu_gen_list, sigma_gen_list, csl, s_scaler_list))).T
    df_res[0] = df_res[0].astype(float)
    df_res[1] = df_res[1].astype(float)
    df_res[2] = df_res[2].astype(float)
    df_res[3] = df_res[3].astype(float)
    df_res[4] = df_res[4].astype(float)

    actions_losses = df_res.rename(columns={0: 'KLD', 1: "Action_Mu", 2: "Action_Sigma", 3: "Cellular State Loss", 4: "Eigenvalues_Scaler"})
    actions_losses['Time Steps'] = actions_losses.index
    # Plotting
    fig, ax = plt.subplots()
    ax.plot(actions_losses.index, actions_losses["Action_Mu"], label='Action_Mu', color='C0')
    ax.plot(actions_losses.index, actions_losses["Action_Sigma"], label='Action_Sigma', color='C1')
    ax.plot(actions_losses.index, actions_losses["Eigenvalues_Scaler"], label='Eigenvalues_Scaler', color='C2')

    ax.legend()
    ax.set_ylabel("Model Training - Actions Space", fontsize=10)
    ax.set_xlabel('Time Steps')
    ax.set_title('Actions Losses over Time')

    return actions_losses



def plot_csl(actions_losses,
             self_state_loss,
             min_reward_bound,
             max_reward_bound,
             max_trajectory_bound,
             min_trajectory_bound):

    fig, ax = plt.subplots()
#     actions_losses['Names'] = names

    ax.plot(actions_losses["Time Steps"], actions_losses["Cellular State Loss"], label="Cellular State Loss")

    ax.axhline(y=max_trajectory_bound, linewidth=2, color='red', linestyle='--')
    ax.axhline(y=max_reward_bound, linewidth=0.5, color='black', linestyle='--')
    ax.axhline(y=self_state_loss, linewidth=0.5, color='green')
    ax.axhline(y=min_reward_bound, linewidth=0.5, color='black', linestyle='--')
    ax.axhline(y=min_trajectory_bound, linewidth=0.5, color='red', linestyle='--')

    ax.axhspan(min_reward_bound, max_reward_bound, color='green', alpha=0.1)
    ax.axhspan(max_reward_bound, max_trajectory_bound, color='red', alpha=0.05)
    ax.axhspan(min_trajectory_bound, min_reward_bound, color='red', alpha=0.05)
    ax.axhspan(min_trajectory_bound, min_reward_bound, color='red', alpha=0.05)
    ax.axhspan(0, min_trajectory_bound, color='red', alpha=0.3)
    ax.axhspan(max_trajectory_bound, max_trajectory_bound+0.005, color='red', alpha=0.05)

    ax.set_ylabel("Cellular State Loss")
    ax.set_xlabel("Time Steps")
    ax.legend()

    plt.show()

# def plot_csl(actions_losses,
#              self_state_loss,
#               min_reward_bound,
#               max_reward_bound,
#               max_trajectory_bound,
#               min_trajectory_bound,
#               file_name, dirctory):
#     face_grid =  sns.lineplot(x="Time Steps",
#                  y="Cellular State Loss",
#                  data=actions_losses)
#     plt.axhline(y=max_trajectory_bound,linewidth=2, color='red', linestyle='--')
# #     plt.axhline(y=max_trajectory_bound*-1,linewidth=2, color='red', linestyle='--')
#
#     plt.axhline(y=max_reward_bound,linewidth=0.5, color='black', linestyle='--')
#     plt.axhline(y=self_state_loss,linewidth=0.5, color='green')
#     plt.axhline(y=min_reward_bound,linewidth=0.5, color='black', linestyle='--')
#
#     plt.axhline(y=min_trajectory_bound,linewidth=0.5, color='red', linestyle='--')
# #     plt.axhline(y=min_trajectory_bound*-1,linewidth=0.5, color='red', linestyle='--')
#     plt.axhspan(min_reward_bound,max_reward_bound, color='green', alpha=0.1)
#     plt.axhspan(max_reward_bound,max_trajectory_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(0,min_trajectory_bound, color='red', alpha=0.3)
#     plt.axhspan(max_trajectory_bound,max_trajectory_bound+0.005, color='red', alpha=0.05)
#     face_grid = sns.displot(y, color="aquamarine")
#     fig = face_grid.figure
#     ax = fig.gca()
#     os.chdir(dirctory)
#     face_grid.figure.savefig((file_name +".pdf"))

# def plot_csl(actions_losses,
#              self_state_loss,
#               min_reward_bound,
#               max_reward_bound,
#               max_trajectory_bound,
#               min_trajectory_bound):
#     face_grid =  sns.lineplot(x="Time Steps",
#                  y="Cellular State Loss",
#                  data=actions_losses)
#     plt.axhline(y=max_trajectory_bound,linewidth=2, color='red', linestyle='--')
# #     plt.axhline(y=max_trajectory_bound*-1,linewidth=2, color='red', linestyle='--')

#     plt.axhline(y=max_reward_bound,linewidth=0.5, color='black', linestyle='--')
#     plt.axhline(y=self_state_loss,linewidth=0.5, color='green')
#     plt.axhline(y=min_reward_bound,linewidth=0.5, color='black', linestyle='--')

#     plt.axhline(y=min_trajectory_bound,linewidth=0.5, color='red', linestyle='--')
# #     plt.axhline(y=min_trajectory_bound*-1,linewidth=0.5, color='red', linestyle='--')
#     plt.axhspan(min_reward_bound,max_reward_bound, color='green', alpha=0.1)
#     plt.axhspan(max_reward_bound,max_trajectory_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(0,min_trajectory_bound, color='red', alpha=0.3)
#     plt.axhspan(max_trajectory_bound,max_trajectory_bound+0.005, color='red', alpha=0.05)
#     # face_grid = sns.displot(y, color="aquamarine")
#     fig = face_grid.figure
#     ax = fig.gca()
#     # os.chdir(dirctory)
#     # face_grid.figure.savefig((file_name +".pdf"))

# def plot_csl(actions_losses, self_state_loss, min_reward_bound, max_reward_bound, max_trajectory_bound, min_trajectory_bound):
#     face_grid = sns.lineplot(x="Time Steps", y="Cellular State Loss", data=actions_losses)
#
#     # Plot dashed lines
#     plt.axhline(y=max_trajectory_bound, linewidth=2, color='red', linestyle='--')
#     plt.axhline(y=max_reward_bound, linewidth=0.5, color='black', linestyle='--')
#     plt.axhline(y=self_state_loss, linewidth=0.5, color='green', label='Self State Loss')
#     plt.axhline(y=min_reward_bound, linewidth=0.5, color='black', linestyle='--')
#     plt.axhline(y=min_trajectory_bound, linewidth=0.5, color='red', linestyle='--')
#
#     # Plot shaded regions
#     plt.axhspan(min_reward_bound, max_reward_bound, color='green', alpha=0.1, label='Reward Bounds')
#     plt.axhspan(max_reward_bound, max_trajectory_bound, color='red', alpha=0.05, label='Trajectory Bounds')
#     plt.axhspan(min_trajectory_bound, min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(0, min_trajectory_bound, color='red', alpha=0.3)
#     plt.axhspan(max_trajectory_bound, max_trajectory_bound + 0.005, color='red', alpha=0.05)
#
#     # Set labels
#     plt.xlabel("Time Steps")
#     plt.ylabel("Cellular State Loss")
#
#     # Display legend
# #     plt.legend()
#
#     # Display the plot
#     plt.show()
#     print("Done")
    # Optionally, save the figure
    # plt.savefig("figure.pdf")
#     return face_grid

# def plot_csl(actions_losses,
#              self_state_loss,
#               min_reward_bound,
#               max_reward_bound,
#               max_trajectory_bound,
#               min_trajectory_bound):
#     face_grid =  sns.lineplot(x="Time Steps",
#                  y="Cellular State Loss",
#                  data=actions_losses)
#     plt.axhline(y=max_trajectory_bound,linewidth=2, color='red', linestyle='--')
# #     plt.axhline(y=max_trajectory_bound*-1,linewidth=2, color='red', linestyle='--')
#
#     plt.axhline(y=max_reward_bound,linewidth=0.5, color='black', linestyle='--')
#     plt.axhline(y=self_state_loss,linewidth=0.5, color='green')
#     plt.axhline(y=min_reward_bound,linewidth=0.5, color='black', linestyle='--')
#
#     plt.axhline(y=min_trajectory_bound,linewidth=0.5, color='red', linestyle='--')
# #     plt.axhline(y=min_trajectory_bound*-1,linewidth=0.5, color='red', linestyle='--')
#     plt.axhspan(min_reward_bound,max_reward_bound, color='green', alpha=0.1)
#     plt.axhspan(max_reward_bound,max_trajectory_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(min_trajectory_bound,min_reward_bound, color='red', alpha=0.05)
#     plt.axhspan(0,min_trajectory_bound, color='red', alpha=0.3)
#     plt.axhspan(max_trajectory_bound,max_trajectory_bound+0.005, color='red', alpha=0.05)
#     face_grid = sns.displot(y, color="aquamarine")
#     face_grid.figure
#     fig.gca()
#     os.chdir(dirctory)
#     face_grid.figure.savefig((file_name +".pdf"))


# ## Cell DRL Enviroment

class CellEnv (Env):

    KL_losses = []
    mu_gen_list = []
    sigma_gen_list = []
    self_state_loss_list = []
    mu_pert_list = []
    s_scaler_list = []
    gen_adatas = []

    def __init__(self):

        # Actions Space
        self.action_space = Box(np.array([-scale, 0.01, 0]),
                                np.array([scale, scale, scale]),
                                dtype=np.float32)

        # Observation Space
        self.observation_space = Box(low=-np.inf,
                                     high=np.inf,
                                     shape=(1,),
                                     dtype=np.float64)
        # Set Trajectory length
        self.Trajectory_length = Trajectory_length
        self.min_max_bound = max_reward_bound - min_reward_bound
        self.csl_distances = list(reversed(np.arange(0,self.min_max_bound, self.min_max_bound/Trajectory_length)))
        self.csl_distances.insert(0, float(self_state_loss[0]))

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

        kl_loss = celldrl.kl_divergence(gen_sm, sf_sm)
        cs_pq_mga = cosine_similarity(np.array([gen_sm]), np.array([sf_sm]))

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
        KL_losses.append(kl_loss)
        mu_gen_list.append(mu_gen)
        sigma_gen_list.append(sigma_gen)
        s_scaler_list.append(s_scaler)
        regularization_list.append(regularization)
        self_state_loss_list.append(cellular_state_loss)
        gen_adatas.append(gen_adata)
        ## Delete gen_adata
        del gen_adata

        # Reduce Trajectory length by 1 step
        self.Trajectory_length -= 1

        # Calculate reward
        if self.state >= min_reward_bound and self.state <=max_reward_bound:

            reward = float (reward_signal + (1-self.state))
        else:
            reward = float(-1)

        # Check if Trajectory is done
        if self.state >=max_trajectory_bound:
            done = True
        elif self.state <=min_trajectory_bound:
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


def MGA (adata, select_by):
    names = []
    si_adatas = []
    si_means = []
    si_m_adatas = []
    timepoints = np.array(adata.obs[select_by].unique())
    for x in timepoints:
        names.append(x)
        si = adata[adata.obs[select_by] == x]
        si_mean = pd.DataFrame(si.X.mean(0)).T
        si_m_adata = ad.AnnData(si_mean)
        si_m_adata.obs = pd.DataFrame(si.obs)[:1]
        si_m_adata.obs_names_make_unique
        si_m_adata.obs[select_by] = si_m_adata.obs[select_by].astype("category")
        si_m_adatas.append(si_m_adata)

    combined_si_m_adatas = ad.concat(si_m_adatas, join="outer")
    combined_si_m_adatas.obs[select_by] = combined_si_m_adatas.obs[select_by].astype("category")
    combined_si_m_adatas.obs["Steps"] = combined_si_m_adatas.obs["Steps"].astype("category")
    combined_si_m_adatas.var_names = adata.var_names

    return  combined_si_m_adatas

def MGA_Realizations (adata, concate_states, env, svd_u_matrix, states_mu,  model, n_realizations, n_gen_cells, n_comp, select_by):

    step =0
    seed = 345

    mu_gen_list_p = []
    sigma_gen_list_p = []
    si_m_adatas_rlz = []
    mga_adatas = []
    names = []
    for x in range (1,n_realizations):
        obs = env.reset()
        while True:
            ## Action Controller
            action, _states = model.predict(obs)
            mu_gen, sigma_gen = action.flatten()[0], abs(action.flatten()[1])
            mu_gen_list_p.append(mu_gen)
            sigma_gen_list_p.append(sigma_gen)
            obs, rewards, done, info = env.step(action)
        #     env.render()
            if done:
                break


    for x in range(0,len(mu_gen_list_p)):
        mu_gen, sigma_gen = mu_gen_list_p[x], sigma_gen_list_p[x]

        ## Action Controller and Generator
        seed +=1
        step +=1
        np.random.seed(seed)
        gen_adata, real_gen_adata, concate_gen_adata = actions_CG (adata = adata,
                                                                   concate_states = concate_states,
                                                                   svd_u_matrix = svd_u_matrix,
                                                                   states_mu = states_mu,
                                                                   n_comp =n_comp,
                                                                   n_gen_cells = n_gen_cells,
                                                                   mu_gen = mu_gen,
                                                                   sigma_gen = sigma_gen,
                                                                   perturb_n_comp = 0,
                                                                   mu_pert = 0,
                                                                   sigma_pert = 1,
                                                                   select_by = select_by)
        del real_gen_adata
        del concate_gen_adata

        steps = (str(step)+"_Step")
        gen_adata.obs["Steps"] = steps
        gen_adata.obs["Steps"] = gen_adata.obs["Steps"].astype("category")
        gen_adata.obs[select_by] = "Generated"

        si_mean = pd.DataFrame(gen_adata.X.mean(0)).T
        si_m_adata = ad.AnnData(si_mean)
        si_m_adata.obs = pd.DataFrame(gen_adata.obs)[:1]
        si_m_adata.obs_names_make_unique
        si_m_adatas_rlz.append(si_m_adata)

        del gen_adata

    timepoints = np.array(adata.obs[select_by].unique())

    for x in timepoints:
        names.append(x)
        si = adata[adata.obs[select_by] == x]
        si_mean = pd.DataFrame(si.X.mean(0)).T
        si_m_adata = ad.AnnData(si_mean)
        si_m_adata.obs = pd.DataFrame(si.obs)[:1]
        si_m_adata.obs_names_make_unique
        mga_adatas.append(si_m_adata)

    mga_adatas = ad.concat(mga_adatas, join="outer")
    si_m_adatas_rlz = ad.concat(si_m_adatas_rlz, join="outer")
    combined_si_m_adatas = ad.concat([mga_adatas,si_m_adatas_rlz], join="outer")
    combined_si_m_adatas.var_names = adata.var_names
    combined_si_m_adatas.obs["Steps"] = combined_si_m_adatas.obs["Steps"].astype("category")

    return mga_adatas, si_m_adatas_rlz, combined_si_m_adatas, mu_gen_list_p, sigma_gen_list_p


def plot_predicted_actions (mu_gen_list_p, sigma_gen_list_p):
    df_res = pd.DataFrame(np.vstack((mu_gen_list_p, sigma_gen_list_p))).T
    # df_res.set_index(0)
    df_res[0]=df_res[0].astype(float)
    df_res[1]=df_res[1].astype(float)
    Pred_actions = df_res.set_axis(["Pred_Action_Mu", "Pred_Action_Sigma"], axis=1, inplace=False)
    Pred_actions.index.name = 'Time Steps'
#     Pred_actions.reshape((10, n_realizations-1))
    face_grid =  sns.lineplot(data=Pred_actions)
    # face_grid = sns.displot(y, color="aquamarine")
    fig = face_grid.figure
    ax = fig.gca()
    return Pred_actions

def plot_model_realizations (mu_gen_list_p, sigma_gen_list_p, n_realizations):

    mu_gen = pd.DataFrame (pd.array(mu_gen_list_p).reshape(10, n_realizations-1))
    sigma_gen = pd.DataFrame (pd.array(sigma_gen_list_p).reshape((10, n_realizations-1)))
    sigma_gen.index.name = 'Time Steps'

    face_grid =  sns.lineplot(data=mu_gen, palette = "Blues")
    # face_grid = sns.displot(y, color="aquamarine")
    plt.ylabel("Predicted actions mu", fontsize=10)
    face_grid.get_legend().remove()
    fig = face_grid.figure
    ax = fig.gca()

    face_grid =  sns.lineplot(data=sigma_gen, palette = "Oranges")
    # face_grid = sns.displot(y, color="aquamarine")
    plt.ylabel("Predicted actions params", fontsize=10)
    face_grid.get_legend().remove()
    fig = face_grid.figure
    ax = fig.gca()


## Functions

def entropy_per_gene (adata, n_genes):
    # gen_sm = softmax(np.median(adata.X, axis=0))
    gen_sm = np.median(adata.X, axis=0)
    gen_prop = gen_sm/ gen_sm.sum(axis=0, keepdims=True)
    entropy_per_gene = entr(gen_prop)

    # plt.plot(gen_prop)
    # plt.plot(entropy_per_gene)
    # plt.show()

    df = pd.DataFrame([entropy_per_gene,adata.var_names]).T
    entropy_asc = df.sort_values(by=0, ascending=True)
    noisy_genes = np.array(entropy_asc[0:n_genes][1])

    entropy_dec = df.sort_values(by=0, ascending=False)
    non_noisy_genes = np.array(entropy_dec[0:n_genes][1])

    return entropy_dec, noisy_genes, non_noisy_genes

def entropy_per_cell (adata):
    # gen_sm = softmax(np.median(adata.X, axis=0))
    gen_sm = np.median(adata.X.T, axis=0)
    gen_prop = gen_sm/ gen_sm.sum(axis=0, keepdims=True)
    entropy_per_cell = entr(gen_prop)
    return entropy_per_cell

def entropy_regularization (p):
    entropy_measure = -np.sum(p * np.log(p))
    return entropy_measure

def RunGAM (adata, n_splines, spline_order, fdr_alpha):

    ## Lists
    gams = []
    # y_preds = []
    p_vals = []
    McFadden_adjs = []
    df = adata.to_df()

    ## Scaling
    scaler = MinMaxScaler(feature_range=(-1, 1))
    df_scaled = scaler.fit_transform(df.to_numpy())
    df = pd.DataFrame(df_scaled, columns=df.columns, index= df.index)

    ## addd pseudotime data to df
    df ["dpt_pseudotime"] = adata.obs["dpt_pseudotime"]
    df = df.sort_values(by=['dpt_pseudotime'])
    for x in np.arange(0, len(adata.var_names)):
        # print(i)
        gam = LinearGAM(s(0, n_splines=n_splines, spline_order=spline_order)).fit(df.iloc[:, x], df ["dpt_pseudotime"])
        gams.append(gam)
        p_val = gam.statistics_['p_values'][0]
        p_vals.append(p_val)
        McFadden_adj = list(gam.statistics_['pseudo_r2'].values())[2]
        McFadden_adjs.append(McFadden_adj)

    fdr_pvals =fdrcorrection(pvals=np.array(p_vals),
                   alpha=fdr_alpha,
                   method='negcorr',
                   is_sorted=False)[1]
    return fdr_pvals, gams, McFadden_adjs


def plot_pseudotime_genes (adata, gene_names,cmap, name, directory):
    df = adata.to_df()
    scaler = MinMaxScaler(feature_range=(-1, 1))
    df_scaled = scaler.fit_transform(df.to_numpy())
    df = pd.DataFrame(df_scaled, columns=df.columns, index= df.index)
    # print(df.shape)
    df["dpt_pseudotime"] = adata.obs["dpt_pseudotime"]
    # df["entropy_per_cell"] = adata.obs["entropy_per_cell"]
    df = df.sort_values(by=['dpt_pseudotime'])




    for gene_name in gene_names:
        x, y = np.array(df ["dpt_pseudotime"]),np.array(df[gene_name])
        # Model fitting
        lowess_model = lowess.Lowess()
        lowess_model.fit(x, y)

        # Model prediction
        x_pred = x
        y_pred = lowess_model.predict(x_pred)
        # Plotting
        plt.plot(x_pred, y_pred, '--', label='LOWESS', color='k', zorder=3)
        plt.scatter(x, y , alpha=1, c=df["dpt_pseudotime"], cmap=cmap, s=3)
        plt.title(gene_name)
        plt.xlabel("Pseudotime")
        plt.ylabel("Gene Expression")
        plt.colorbar()
        plt.show()
        os.chdir(directory)
        plt.savefig(name)


def plot_pseudotime_Modules (adata, n_Modules,
                             # K_pred_modules,
                             som_pred_modules ,
                             cmap):

    module_names = []

    for module_number in range(0, n_Modules):
        # print(module_number)
        # Module_genes = np.array((K_pred_modules[K_pred_modules.Module == module_number]).Genes)
        # score_name = ('Kmeans_Module_'+str(module_number))
        # module_names.append(score_name)
        # sc.tl.score_genes(adata, Module_genes, score_name=score_name)
        Module_genes = np.array((som_pred_modules[som_pred_modules.Module == module_number]).Genes)
        score_name = ('Module_'+str(module_number))
        module_names.append(score_name)
        sc.tl.score_genes(adata, Module_genes, score_name=('Module_'+str(module_number)))

    # module_names.append("dpt_pseudotime")
    Modules_scores = adata.obs[np.array(module_names)]
    scaler = MinMaxScaler(feature_range=(-1, 1))
    Modules_scores_scaled = scaler.fit_transform(Modules_scores.to_numpy())
    Modules_scores = pd.DataFrame(Modules_scores_scaled, columns=Modules_scores.columns, index= Modules_scores.index)

    Modules_scores["dpt_pseudotime"] = adata.obs["dpt_pseudotime"]
    Modules_scores = Modules_scores.sort_values(by=['dpt_pseudotime'])

    for module in module_names[ : -1]:
        # print(module)

        x, y = np.array(Modules_scores ["dpt_pseudotime"]),np.array(Modules_scores[module])
        # Model fitting
        lowess_model = lowess.Lowess()
        lowess_model.fit(x, y)

        # Model prediction
        x_pred = x
        y_pred = lowess_model.predict(x_pred)
        plt.scatter(x, y , alpha=1, c=Modules_scores["dpt_pseudotime"], cmap=cmap, s=3)
        # Plotting
        plt.plot(x_pred, y_pred, '--', label='LOWESS', color='k', zorder=3)
        # plt.legend(["Pseudotime_Values"])
        # plt.legend(['First line', 'Second line'])
        plt.title(module)
        plt.xlabel("Pseudotime")
        plt.ylabel("Module Expression")
        plt.colorbar()
        plt.show()

    return Modules_scores, module_names


def modules_discovery(adata, fdr_pvals, m, McFadden_adjs, adj_pval_thr, n, Top_pseudotime_genes):
    pval_df = pd.DataFrame([adata.var_names, fdr_pvals, McFadden_adjs], index= ["Genes","adj_pvalues","adj_R_squared"]).T
    pval_filtered = pval_df[pval_df["adj_pvalues"] <adj_pval_thr]
    sig_genes= np.array((pval_filtered.sort_values(by="adj_R_squared",
                                                          ascending = False)).iloc[:Top_pseudotime_genes]["Genes"])
    sig_pseudotime_adata = adata[:, sig_genes]
    sig_pseudotime_genes = sig_pseudotime_adata.X.T

    ## SOM
    pseudo_gene_som = SOM(m=m, n=n, dim=adata[:, sig_genes].X.shape[0])
    pseudo_gene_som.fit(sig_pseudotime_genes)
    predictions = pseudo_gene_som.predict(sig_pseudotime_genes)
    som_pred_modules = pd.DataFrame([sig_pseudotime_adata.var_names, predictions], index=["Genes", "Module"]).T
    som_pred_modules = som_pred_modules.sort_values(by="Module")
    return som_pred_modules, sig_genes

def plot_Modules_Heatmaps (adata, n_Modules,
                             # K_pred_modules,
                             som_pred_modules ,
                            select_by,
                             cmap):

    module_names = []

    for module_number in range(0, n_Modules):
        # print(module_number)
        # Module_genes = np.array((K_pred_modules[K_pred_modules.Module == module_number]).Genes)
        # score_name = ('Kmeans_Module_'+str(module_number))
        # module_names.append(score_name)
        # sc.tl.score_genes(adata, Module_genes, score_name=score_name)
        Module_genes = np.array((som_pred_modules[som_pred_modules.Module == module_number]).Genes)
        score_name = ('Module_'+str(module_number))
        print(score_name)
        scv.pl.heatmap(adata, var_names=Module_genes,
               sortby='dpt_pseudotime',
               col_color=[select_by, 'dpt_pseudotime'],
               color_map = cmap,
               colorbar = True,
               # palette = ['viridis', 'RdBu_r'],
               n_convolve=200)




def optimum_actions_path (adata, concate_states, env, svd_u_matrix, s ,
                          states_mu,  model, n_realizations, n_gen_cells,
                          n_comp, select_by, regularization_type):

    step =0
    seed = 345

    mu_gen_list_p = []
    sigma_gen_list_p = []
    s_scalers_list_p = []
    actions_list_p = []
    self_state_loss_list_p = []
    cellular_state_losses = []

    for x in range (0,n_realizations):
        obs = env.reset()

        while True:

            ## Action Controller
            action, _state = model.predict(obs, deterministic=True)
            mu_gen, sigma_gen, s_scaler = action.flatten()[0], abs(action.flatten()[1]), action.flatten()[2]

            actions_list_p.append(action)
            s_scalers_list_p.append(s_scaler)
            mu_gen_list_p.append(mu_gen)
            sigma_gen_list_p.append(sigma_gen)

            obs, rewards, done, info = env.step(action)
            if done:
                break


    for x in range(0,len(mu_gen_list_p)):
        # print(x)
        mu_gen, sigma_gen, s_scaler = mu_gen_list_p[x], sigma_gen_list_p[x], s_scalers_list_p[x]

        ## Action Controller and Generator
        seed +=1
        step +=1
        np.random.seed(seed)
        gen_adata, real_gen_adata, concate_gen_adata = celldrl.actions_prediction (adata = adata,
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




        gen_sm = softmax(np.median(gen_adata.X, axis=0))
        sf_sm = softmax(np.median(sf.X, axis=0))


        kl_loss = celldrl.kl_divergence(gen_sm, sf_sm)
        cs_pq_mga = cosine_similarity(np.array([gen_sm]), np.array([sf_sm]))

        if regularization_type == 'entropy':
            entropy_rg = celldrl.entropy_regularization(gen_sm)
            regularization = lammda * entropy_rg
        elif regularization_type == 'l1':
            regularization = lammda * sum(abs(gen_sm))
        elif regularization_type == 'l2':
            regularization = lammda * sum(pow(gen_sm, 2))
        elif regularization_type == 'None':
            regularization = 0

        cellular_state_loss =  (1- cs_pq_mga) * theta * kl_loss + regularization
        cellular_state_losses.append(cellular_state_loss)

        del gen_adata
        del real_gen_adata
        del concate_gen_adata

    return actions_list_p, cellular_state_losses


def plot_predicted_actions (actions_list_p):
    df_res = pd.DataFrame(np.vstack((actions_list_p)))
    # df_res.set_index(0)
    df_res[0]=df_res[0].astype(float)
    df_res[1]=df_res[1].astype(float)
    df_res[2]=df_res[2].astype(float)
    Pred_actions = df_res.set_axis(["Pred_Action_Mu", "Pred_Action_Sigma", "Pred_Action_Scalers"], axis=1, inplace=False)
    Pred_actions.index.name = 'Time Steps'
#     Pred_actions.reshape((10, n_realizations-1))
    face_grid =  sns.lineplot(data=Pred_actions)
    # face_grid = sns.displot(y, color="aquamarine")
    fig = face_grid.figure
    ax = fig.gca()
    return Pred_actions



# class CellEnv (Env):
#     def __init__(self, adata, states_mu, sf, s, concate_states, svd_u_matrix, n_comp, Trajectory_length,scale, n_gen_cells, norm, lammda, theta, total_timesteps,reward_signal,select_by,regularization_type, self_state_loss, max_reward_bound, min_reward_bound,max_trajectory_bound,min_trajectory_bound, seed):
#
#         self.adata = adata
#         self.concate_states = concate_states,
#         self.svd_u_matrix = pd.DataFrame(svd_u_matrix),
#         self.states_mu = states_mu,
#         self.s = s,
#         self.sf = sf
#         self.n_comp = n_comp
#         self.seed = seed
#         self.Trajectory_length = Trajectory_length
#         self.scale = scale
#         self.n_gen_cells = n_gen_cells
#         self.norm = norm
#         self.lammda = lammda
#         self.theta =  theta
#         self.total_timesteps = total_timesteps
#         self.reward_signal = reward_signal
#         self.select_by = select_by
#         self.regularization_type = regularization_type
#         self.self_state_loss = self_state_loss
#         self.max_reward_bound =max_reward_bound
#         self.min_reward_bound = min_reward_bound
#         self.max_trajectory_bound = max_trajectory_bound
#         self.min_trajectory_bound = min_trajectory_bound
#
#         # Actions Space
#         self.action_space = Box(np.array([-scale, 0.01, 0]),
#                                 np.array([scale, scale, scale]),
#                                 dtype=np.float32)
#
#         # Observation Space
#         self.observation_space = Box(low=-np.inf,
#                                      high=np.inf,
#                                      shape=(1,),
#                                      dtype=np.float64)
#         # Define initial state and other environment-specific variables
#
#         self.min_max_bound = self.max_reward_bound - self.min_reward_bound
#         self.csl_distances = list(reversed(np.arange(0,self.min_max_bound, self.min_max_bound/Trajectory_length)))
#         self.csl_distances.insert(0, float(self.self_state_loss[0]))
#         self.sf_sm = softmax(np.median(sf.X, axis=0))
#
#         # Create a list as a class attribute
#         self.regularization_list = []
#         self.KL_losses = []
#         self.mu_gen_list = []
#         self.sigma_gen_list = []
#         self.self_state_loss_list = []
#         self.KL_losses = []
#         self.mu_gen_list = []
#         self.sigma_gen_list = []
#         self.s_scaler_list = []
#         self.self_state_loss_list = []
#         self.mu_pert_list = []
#         self.sigma_pert_list = []
#         self.gen_adatas = []
#
#
#
#     def reset(self):
#         # Reset Trajectory observation space
#         self.state = np.array([random.uniform(0,0.05)]).astype(float)
#         # Reset Trajectory time
#         self.Trajectory_length = self.Trajectory_length
#         return self.state
#
#     def step(self, action):
#         mu_gen, sigma_gen, s_scaler = action[0], abs(action[1]), action[2]
#         print(type(self.svd_u_matrix))
#         svd_u_matrix = np.reshape(self.svd_u_matrix, (self.adata.n_vars, self.n_comp))
#         print(svd_u_matrix.shape)
#
#         gen_adata = actions_training (adata = self.adata,
#                                                concate_states = self.concate_states,
#                                                svd_u_matrix = svd_u_matrix,
#                                                s = self.s,
#                                                s_scaler = s_scaler,
#                                                states_mu = self.states_mu,
#                                                n_comp =self.n_comp,
#                                                n_gen_cells = self.n_gen_cells,
#                                                mu_gen = mu_gen,
#                                                sigma_gen = sigma_gen,
#                                                select_by = self.select_by,
#                                                norm = self.norm)
#
#         gen_adata.obs[select_by] = "Generated"
#
#         ## Calculate KLD and Cosine Similarity:
#         gen_sm = softmax(np.median(gen_adata.X, axis=0))
#
#         kl_loss = kl_divergence(gen_sm, self.sf_sm)
#         cs_pq_mga = cosine_similarity(np.array([gen_sm]), np.array([self.sf_sm]))
#
#         if regularization_type == 'entropy':
#             entropy_rg = celldrl.entropy_regularization(gen_sm)
#             regularization = lammda * entropy_rg
#         elif regularization_type == 'l1':
#             regularization = lammda * sum(abs(gen_sm))
#         elif regularization_type == 'l2':
#             regularization = lammda * sum(pow(gen_sm, 2))
#         elif regularization_type == 'None':
#             regularization = 0
#
#         # print(regularization)
#         cellular_state_loss =  (1- cs_pq_mga) * theta * kl_loss + regularization
#
#         ## Update Self State by the current observations
#
#         self.state = cellular_state_loss.flatten()
#
#         ## Collect lists
#         self.KL_losses.append(kl_loss)
#         self.mu_gen_list.append(mu_gen)
#         self.sigma_gen_list.append(sigma_gen)
#         self.s_scaler_list.append(s_scaler)
#         self.regularization_list.append(regularization)
#         self.self_state_loss_list.append(cellular_state_loss)
#         self.gen_adatas.append(gen_adata)
#         ## Delete gen_adata
#         del gen_adata
#
#         # Reduce Trajectory length by 1 step
#         self.Trajectory_length -= 1
#
#         # Calculate reward
#         if self.state >= self.min_reward_bound and self.state <=self.max_reward_bound:
#
#             reward = float (reward_signal + (1-self.state))
#         else:
#             reward = float(-1)
#
#         # Check if Trajectory is done
#         if self.state >=self.max_trajectory_bound:
#             done = True
#         elif self.state <=self.min_trajectory_bound:
#             done = True
#         elif self.Trajectory_length <= 0:
#             done = True
#         else:
#             done = False
#         info = {}
#
#         # Return step information
#         return self.state, reward, done, info
#
#     def render(self):
#         pass
#
# if __name__ == "__main__":
#     env = CellEnv()


# register(
#     id='CellEnv-v0',
#     entry_point='celldrl:CellEnv',
#     kwargs={
#         'adata': adata,
#         'states_mu': states_mu,
#         's':s,
#         'self_state_loss':self_state_loss,
#         'concate_states':concate_states,
#         'svd_u_matrix':svd_u_matrix,
#         'sf': sf,
#         'self_state_loss': self_state_loss,
#         'n_comp': 100,
#         'Trajectory_length': 10,
#         'scale': 10,
#         'n_gen_cells': n_gen_cells,
#         'norm':"max",
#         'lammda': 0.001,
#         'theta': 1,
#         'total_timesteps': 1000,
#         'reward_signal': 20,
#         'select_by': select_by,
#         'max_reward_bound': max_reward_bound,
#         'min_reward_bound': min_reward_bound,
#         'max_trajectory_bound': max_trajectory_bound,
#         'min_trajectory_bound': min_trajectory_bound,
#         'regularization_type': 'entropy',
#         'seed': 345
#     }
# )


def generate_trajectory(env, model, adata, concate_states,svd_u_matrix,s, sf, states_mu, n_comp , theta, n_gen_cells, select_by, norm , seed):

    gen_adata_list = []
    actions_list = []
    KL_losses_p = []
    mu_gen_list_p = []
    sigma_gen_list_p = []
    self_state_loss_list_p = []
    step = 0
 
    # obs = env.reset()
    obs, info = env.reset()
    done = False
    score = 0
    print ("Cell-DRL Agent is Generating novel cellular states ...")

    #while True:
    while not done:

        # action, _states = model.predict(obs)
        action, _state = model.predict(obs, deterministic=True)
        actions_list.append(action)
        mu_gen, sigma_gen, s_scaler = action.flatten()[0], abs(action.flatten()[1]), action.flatten()[2]

    #     print( mu_gen, sigma_gen, sigma_pert)
        print( mu_gen, sigma_gen, s_scaler)

        ## Action Controller and Generator
        seed +=1
        step +=1

        np.random.seed(seed)

        gen_adata, real_gen_adata, concate_gen_adata = actions_prediction (adata = adata,
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

        steps = ("Step "+str(step))
        gen_adata.obs["Steps"] = steps
        gen_adata.obs["Steps"] = gen_adata.obs["Steps"].astype("category")
        gen_adata.obs[select_by] = "Generated"
        ## Calculate KLD and Cosine Similarity:

        gen_sm = softmax(np.median(gen_adata.X, axis=0))
        sf_sm = softmax(np.median(sf.X, axis=0))

        gen_state_Loss = kl_divergence(gen_sm, sf_sm)

        cs_pq_mga = cosine_similarity(np.array([gen_sm]), np.array([sf_sm]))
        cellular_state_loss = (1-cs_pq_mga) * gen_state_Loss * theta
        self_state_loss_list_p.append(cellular_state_loss)

        ## Collect lists
        KL_losses_p.append(gen_state_Loss)
        mu_gen_list_p.append(mu_gen)
        sigma_gen_list_p.append(sigma_gen)
        gen_adata_list.append(gen_adata)
        
        # obs, rewards, done, info = env.step(action)
        # Take a step in the environment
        obs, reward, terminated, truncated, info = env.step(action)
    #     env.render()

    # Combine terminated or truncated to get the "done" flag
        done = terminated or truncated
        if done:
            print('info', info)
            break
    print("Cell-DRL Agent Generated The Predicted Cellular States Trajectory")

    return gen_adata_list


def train_agent(env, total_timesteps, log_path):

    check_env(env)
    print("CellEnv check is DONE")

    # Wrap the environment in DummyVecEnv
    env = DummyVecEnv([lambda: env])

    print("Cell-DRL Agent Training Started")
    model = SAC("MlpPolicy", env, verbose=0, tensorboard_log=log_path)

    start_time = time.time()
    model.learn(total_timesteps=total_timesteps)
    end_time = time.time()

    elapsed_time = (end_time - start_time) / 60  # Convert to minutes
    print("Cell-DRL Training is DONE")
    print(f"Training completed in {elapsed_time:.2f} minutes")

    return model



def process_and_combine_data(adata, gen_adata_list, select_by, max_value, n_neighbors, n_pcs, min_dist):

    # Add "Steps" column to adata.obs
    adata.obs["Steps"] = adata.obs[select_by]

    # Combine generated data with real data
    combined = ad.concat(gen_adata_list, join="outer").copy()
    combined.obs_names_make_unique()
    sc.pp.scale(combined, max_value=10)
    combined.X = np.nan_to_num(combined.X)

    # Concatenate combined data with original data
    final_adata = ad.concat([combined, adata], join="outer").copy()
    final_adata.obs_names_make_unique()

    # Perform dimensionality reduction using celldrl
    final_adata = dim_reduction(
        final_adata,
        n_neighbors=n_neighbors,
        n_pcs=n_pcs,
        min_dist=min_dist
    )

    return final_adata


print("Cell-DRL Package is loaded Successfully ...")
