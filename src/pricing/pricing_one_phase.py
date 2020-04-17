import numpy as np
import matplotlib.pyplot as plt
from src.pricing.environment import *
from src.pricing.greedy_learner import *
from src.pricing.ts_learner import *
from src.pricing.reward_function import rewards

T = 100

n_experiments = 100

min_budget = 0.0
max_budget = 1.0

n_arms = int(np.ceil(np.power(np.log2(T) * T, 1 / 4)))

subcampaigns = [0, 1, 2]
conversion_prices = np.linspace(min_budget, max_budget, n_arms)
rewards = rewards(conversion_prices)
n_arms = len(rewards)
opt = np.max(rewards)

environments = []

ts_rewards_per_experiment = []
gr_rewards_per_experiment = []

for subcampaign in range(len(subcampaigns)):
    ts_rewards_per_experiment.append([])
    gr_rewards_per_experiment.append([])

for e in range(0, n_experiments):

    gr_learners = []
    ts_learners = []

    for subcampaign in range(len(subcampaigns)):
        environments.append(Environment(n_arms=n_arms, probabilities=rewards))
        ts_learners.append(TS_Learner(n_arms=n_arms))
        gr_learners.append(Greedy_Learner(n_arms=n_arms))
    for t in range(0, T):
        # Thompson Sampling Learner
        for subcampaign in range(len(subcampaigns)):
            pulled_arm = ts_learners[subcampaign].pull_arm()
            reward = environments[subcampaign].round(pulled_arm)
            ts_learners[subcampaign].update(pulled_arm, reward)

        # Greedy Learner
        for subcampaign in range(len(subcampaigns)):
            pulled_arm = gr_learners[subcampaign].pull_arm()
            reward = environments[subcampaign].round(pulled_arm)
            gr_learners[subcampaign].update(pulled_arm, reward)

    for subcampaign in range(len(subcampaigns)):
        ts_rewards_per_experiment[subcampaign].append(ts_learners[subcampaign].collected_rewards)
        gr_rewards_per_experiment[subcampaign].append(gr_learners[subcampaign].collected_rewards)

fig, axs = plt.subplots(3, 2)
for subcampaign in range(len(subcampaigns)):
    # axs[subcampaign, 0].figure("subcampaign" + str(subcampaign) + ".1")
    axs[subcampaign, 0].plot(np.cumsum(np.mean(np.array(opt) - ts_rewards_per_experiment[subcampaign], axis=0)), 'r')
    axs[subcampaign, 0].plot(np.cumsum(np.mean(np.array(opt) - gr_rewards_per_experiment[subcampaign], axis=0)), 'g')
    axs[subcampaign, 0].legend(["TS", "Greedy"])

    # axs.figure("subcampaign" + str(subcampaign) + ".2")
    axs[subcampaign, 1].plot((np.mean(np.array(opt) - ts_rewards_per_experiment[subcampaign], axis=0)), 'r')
    axs[subcampaign, 1].plot((np.mean(np.array(opt) - gr_rewards_per_experiment[subcampaign], axis=0)), 'g')
    axs[subcampaign, 1].legend(["TS", "Greedy"])

for ax in axs.flat:
    if list(axs.flat).index(ax) % 2 == 0:
        ax.set(xlabel='t', ylabel='CumRegret')
    else:
        ax.set(xlabel='t', ylabel='Regret')
    # ax.label_outer()

plt.show()
