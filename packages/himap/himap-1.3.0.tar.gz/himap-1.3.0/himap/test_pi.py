from base import GaussianHSMM, MOD_Hsmm
import os
import sys

from plot import plot_zoomed_ruls, plot_multiple_obs
from utils import get_state_prob

#fixme: somehow obs and states have different lengths

results_path = os.path.join(os.path.dirname(__file__), 'results', 'models')

n_states = 6
num_histories = 20

hsmm_init = MOD_Hsmm(n_states=n_states, n_durations=260, f_value=60, obs_state_len=10)
hsmm_init_norm = GaussianHSMM(n_states=n_states, n_durations=260, f_value=60, obs_state_len=10, name="norm")

obs, states = hsmm_init.mc_dataset(num_histories, timesteps=1000)
hsmm_init_norm._init_mc()
# hsmm_estim = GaussianHSMM(n_states=n_states,
#                           n_durations=hsmm_init.n_durations,
#                           f_value=hsmm_init.f_value,
#                           obs_state_len=hsmm_init.obs_state_len,
#                           left_to_right=False
#                           )

# hsmm_estim.fit(obs)
# hsmm_estim.save_model()

# hsmm_estim.load_model("hsmm")

# hsmm_init.prog_init_pi(obs)
state_prob = get_state_prob(hsmm_init, obs)
pdf_ruls_all, mean_rul_per_step, upper_rul_per_step, lower_rul_per_step, state_prob = hsmm_init.prognostics(obs,
                                                                                                            plot_rul=True,
                                                                                                            w_RUL=True)
pdf_ruls_all_old, mean_rul_per_step_old, upper_rul_per_step_old, lower_rul_per_step_old = hsmm_init_norm.prognostics(
    obs, plot_rul=True)
# pdf_ruls_all_mod_old, mean_rul_per_step_mod_old, upper_rul_per_step_mod_old, lower_rul_per_step_mod_old, _ = hsmm_init.prognostics(
#     obs, plot_rul=True, w_RUL=False)

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# i=3
# plt.figure()
# plt.plot(pdf_ruls_all_old[f'traj_{i}']['timestep_2'], label='first_state_known', color='tab:blue', linewidth=2,alpha=0.7)
# plt.plot(pdf_ruls_all[f'traj_{i}']['timestep_2'], label='first_state_unknown', color='tab:red', linewidth=2,alpha=0.7)
# plt.legend()
# plt.show()

# RUL[timesteps,sample] - for single trajectory
techniques = ['RUL_new', 'RUL_viterbi', 'RUL_mod_old']
labels = ['RUL_online', 'RUL_viterbi', 'RUL_mod_old']
rmse = []
mean_RUL_dict, LB_RUL_dict, UB_RUL_dict, true_RUL_dict = {}, {}, {}, {}

mean_RUL_dict['RUL_new'] = mean_rul_per_step
mean_RUL_dict['RUL_viterbi'] = mean_rul_per_step_old
# mean_RUL_dict['RUL_mod_old'] = mean_rul_per_step_mod_old
LB_RUL_dict['RUL_new'] = lower_rul_per_step
LB_RUL_dict['RUL_viterbi'] = lower_rul_per_step_old
# LB_RUL_dict['RUL_mod_old'] = lower_rul_per_step_mod_old
UB_RUL_dict['RUL_new'] = upper_rul_per_step
UB_RUL_dict['RUL_viterbi'] = upper_rul_per_step_old
# UB_RUL_dict['RUL_mod_old'] = upper_rul_per_step_mod_old

plot_zoomed_ruls(mean_RUL_dict, LB_RUL_dict, UB_RUL_dict, techniques, labels)
plot_multiple_obs(obs, states, num2plot=2)

print('1')
