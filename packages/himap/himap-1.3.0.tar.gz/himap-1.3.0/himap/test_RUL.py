import numpy as np
from sklearn.linear_model import LinearRegression
from itertools import zip_longest


n_states=3

dur_mat=[[0,0,0,0.1,0.1,0.3,0.3,0.1,0.1,0],[0,0,0,0.1,0.1,0.1,0.3,0.3,0.1,0],[0,0,0,0.1,0.1,0.1,0.1,0.3,0.3,0]]

dur_mat=np.array(dur_mat)

viterbi=[0,0,0,0,0,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2]
gamma_prob=[[0.7,0.3,0],[0.65,0.35,0],[0.6,0.4,0],[0.6,0.4,0],[0.6,0.4,0],
            [0.4,0.6,0],[0.3,0.7,0],[0,1,0],[0,1.,0],[0,1.,0],
            [0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],
            [0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]]
gamma_prob=np.array(gamma_prob)


viterbi_states=viterbi
max_samples=5000
last_observed=True
equation = 1


RUL = np.zeros((len(viterbi_states), max_samples))
mean_RUL, LB_RUL, UB_RUL = (np.zeros(len(viterbi_states)) for _ in range(3))
dur = dur_mat
prev_state, stime = 0, 0


for (i, state),prob in zip(enumerate(viterbi_states),gamma_prob):
    # Process primary state and additional states with probability > 1e-5
    states_to_process = [state]
    additional_states = np.where(prob > 1e-5)[0]
    for alt_state in additional_states:
        if alt_state != state:
            states_to_process.append(alt_state)

    weighted_rul = np.zeros(max_samples)

    for state_idx, process_state in enumerate(states_to_process):
        first, second = (np.zeros_like(dur[0, :]) for _ in range(2))
        first[1] = second[1] = 1
        cdf_curr_state = np.cumsum(dur[process_state, :])
        if process_state == prev_state:
            stime += 1
        else:
            prev_state = process_state
            stime = 1

        if stime < len(cdf_curr_state):
            d_value = cdf_curr_state[stime]
        else:
            d_value = cdf_curr_state[-1]

        available_states = np.arange(process_state, n_states - 1)

        for j in available_states:
            if j != available_states[-1]:
                first = np.convolve(first, dur[j, :])
                second = np.convolve(second, dur[j + 1, :])

            else:
                first = np.convolve(first, dur[j, :])

        if equation == 1:
            first_red = np.zeros_like(first)
            first_red = first[stime:]

            # make sure that after subtracting the soujourn time from the pmf of the first term, that it still sums to 1
            if first_red.sum() != 1:
                first_red[0] = first_red[0] + (1 - first_red.sum())

        else:
            first_red = first

        first_red = first_red * (1 - d_value)
        second = second * d_value

        result = np.array([sum(n) for n in zip_longest(first_red, second, fillvalue=0)])

        # Get probability weight for this state
        state_prob = prob[process_state]

        # Add weighted result to accumulated RUL
        if len(result) < max_samples:
            weighted_rul[:len(result)] += result * state_prob
        else:
            weighted_rul += result[:max_samples] * state_prob

    if available_states.size > 0 or not last_observed:
        RUL[i, :] = weighted_rul
        cdf_curr_RUL = np.cumsum(RUL[i, :])

        # LB RUL
        X, y = [], []
        for l, value in enumerate(cdf_curr_RUL):
            if value > 0.05:
                X = [cdf_curr_RUL[l - 1], value]
                y = [l - 1, l]
                break
        X = np.asarray(X).reshape(-1, 1)
        y = np.asarray(y).reshape(-1, 1)
        LB_RUL[i] = LinearRegression().fit(X, y).predict(np.asarray(0.05).reshape(-1, 1))

        # UB RUL
        X, y = [], []
        for l, value in enumerate(cdf_curr_RUL):
            if value > 0.95:
                X = [cdf_curr_RUL[l - 1], value]
                y = [l - 1, l]
                break
        X = np.asarray(X).reshape(-1, 1)
        y = np.asarray(y).reshape(-1, 1)
        UB_RUL[i] = LinearRegression().fit(X, y).predict(np.asarray(0.95).reshape(-1, 1))

        # mean RUL
        value = np.arange(0, RUL.shape[1])
        mean_RUL[i] = sum(RUL[i, :] * value)

    elif not available_states.size > 0 and last_observed:
        RUL[i, :], mean_RUL[i], UB_RUL[i], LB_RUL[i] = 0, 0, 0, 0
        mean_RUL = np.hstack((np.delete(mean_RUL, mean_RUL == 0), np.array((0))))
        UB_RUL = np.hstack((np.delete(UB_RUL, UB_RUL == 0), np.array((0))))
        LB_RUL = np.hstack((np.delete(LB_RUL, LB_RUL == 0), np.array((0))))
        break

####old RUL
RUL_old = np.zeros((len(viterbi_states), max_samples))
mean_RUL_old, LB_RUL_old, UB_RUL_old = (np.zeros(len(viterbi_states)) for _ in range(3))
dur = dur_mat
prev_state, stime = 0, 0
for i, state in enumerate(viterbi_states):
    first, second = (np.zeros_like(dur[0, :]) for _ in range(2))
    first[1] = second[1] = 1
    cdf_curr_state = np.cumsum(dur[state, :])
    if state == prev_state:
        stime += 1
    else:
        prev_state = state
        stime = 1

    if stime < len(cdf_curr_state):
        d_value = cdf_curr_state[stime]
    else:
        d_value = cdf_curr_state[-1]

    available_states = np.arange(state, n_states - 1)

    for j in available_states:
        if j != available_states[-1]:
            first = np.convolve(first, dur[j, :])
            second = np.convolve(second, dur[j + 1, :])

        else:
            first = np.convolve(first, dur[j, :])

    if equation == 1:
        first_red = np.zeros_like(first)
        first_red = first[stime:]

        # make sure that after subtracting the soujourn time from the pmf of the first term, that it still sums to 1
        if first_red.sum() != 1:
            first_red[0] = first_red[0] + (1 - first_red.sum())

    else:
        first_red = first

    first_red = first_red * (1 - d_value)
    second = second * d_value

    result = [sum(n) for n in zip_longest(first_red, second, fillvalue=0)]

    if available_states.size > 0 or not last_observed:

        RUL_old[i, :] = [sum(n) for n in zip_longest(RUL_old[i, :], result, fillvalue=0)]
        cdf_curr_RUL = np.cumsum(RUL_old[i, :])

        # UB RUL
        X, y = [], []
        for l, value in enumerate(cdf_curr_RUL):
            if value > 0.05:
                X = [cdf_curr_RUL[l - 1], value]
                y = [l - 1, l]
                break
        X = np.asarray(X).reshape(-1, 1)
        y = np.asarray(y).reshape(-1, 1)
        LB_RUL_old[i] = LinearRegression().fit(X, y).predict(np.asarray(0.05).reshape(-1, 1))

        # LB RUL
        X, y = [], []
        for l, value in enumerate(cdf_curr_RUL):
            if value > 0.95:
                X = [cdf_curr_RUL[l - 1], value]
                y = [l - 1, l]
                break
        X = np.asarray(X).reshape(-1, 1)
        y = np.asarray(y).reshape(-1, 1)
        UB_RUL_old[i] = LinearRegression().fit(X, y).predict(np.asarray(0.95).reshape(-1, 1))

        # mean RUL
        value = np.arange(0, RUL_old.shape[1])
        mean_RUL_old[i] = sum(RUL_old[i, :] * value)

    elif not available_states.size > 0 and last_observed:
        RUL_old[i, :], mean_RUL_old[i], UB_RUL_old[i], LB_RUL_old[i] = 0, 0, 0, 0
        mean_RUL_old = np.hstack((np.delete(mean_RUL_old, mean_RUL_old == 0), np.array((0))))
        UB_RUL_old = np.hstack((np.delete(UB_RUL_old, UB_RUL_old == 0), np.array((0))))
        LB_RUL_old = np.hstack((np.delete(LB_RUL_old, LB_RUL_old == 0), np.array((0))))
        break

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# RUL[timesteps,sample] - for single trajectory
techniques=['RUL_new','RUL_old']
labels=['TD expression','TI expression']
rmse=[]
mean_RUL_dict, LB_RUL_dict, UB_RUL_dict, true_RUL_dict = {}, {}, {}, {}


mean_RUL_dict['RUL_new'] = mean_RUL
mean_RUL_dict['RUL_old'] = mean_RUL_old
LB_RUL_dict['RUL_new'] = LB_RUL
LB_RUL_dict['RUL_old'] = LB_RUL_old
UB_RUL_dict['RUL_new'] = UB_RUL
UB_RUL_dict['RUL_old'] = UB_RUL_old

colors= ['tab:blue', 'tab:green']
fig, ax = plt.subplots(figsize=(19, 10))
true_RUL = np.arange(len(mean_RUL_dict[techniques[0]]) - 1, -1, -1)
ax.plot(true_RUL, label='True RUL', color='black', linewidth=2)
for i in range(len(techniques)):
    mean_RUL = mean_RUL_dict[techniques[i]]
    LB_RUL = LB_RUL_dict[techniques[i]]
    UB_RUL = UB_RUL_dict[techniques[i]]
    ax.plot(mean_RUL, '--', label=f'Mean Predicted RUL {labels[i]}', color=colors[i], linewidth=2)
    ax.plot(UB_RUL, '-.', label=f'Lower Bound (90% CI) {labels[i]}', color=colors[i], linewidth=1)
    ax.plot(LB_RUL, '-.', label=f'Upper Bound (90% CI) {labels[i]}', color=colors[i], linewidth=1)
    ax.fill_between(np.arange(0, len(UB_RUL)), UB_RUL, LB_RUL, alpha=0.1, color=colors[i])
    fig.suptitle('RUL')
    ax.legend(loc='best')
    ax.set_xlabel('Time')
    ax.set_ylabel('Remaining Useful Life')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)