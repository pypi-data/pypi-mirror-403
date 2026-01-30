__version__ = "0.1.0"

from gymnasium.envs.registration import register


register(
    id='celldrl/CellDRL-v0',
    entry_point='celldrl.envs:CellEnv',
    # kwargs={
    #     'sf': sf,
    #     'self_state_loss': self_state_loss,
    #     'n_comp': 100,
    #     'Trajectory_length': 10,
    #     'scale': 10,
    #     'n_gen_cells': sf.shape[0],
    #     'norm':"max",
    #     'lammda': 0.001,
    #     'theta': 1,
    #     'total_timesteps': 1000,
    #     'reward_signal': 20,
    #     'select_by': select_by,
    #     'max_reward_bound': max_reward_bound,
    #     'min_reward_bound': min_reward_bound,
    #     'max_trajectory_bound': max_trajectory_bound,
    #     'min_trajectory_bound': min_trajectory_bound,
    #     'regularization_type': 'entropy',
    #     'seed': 345
    # }
)

# register(
#     id='celldrl/CellEnv-v0',
#     entry_point='celldrl.envs:CellEnv', 
#     kwargs={
#         'sf': sf,
#         'self_state_loss': self_state_loss,
#         'n_comp': 100,
#         'Trajectory_length': 10,
#         'scale': 10,
#         'n_gen_cells': sf.shape[0],
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