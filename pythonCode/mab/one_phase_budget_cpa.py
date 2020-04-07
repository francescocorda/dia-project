import time
import matplotlib.pyplot as plt
from pythonCode.mab.Environment.ClickBudget import *
from pythonCode.mab.Learner.GPTS_Learner import *
from pythonCode.mab.not_used.Knapsack import *
from pythonCode.mab.Solver.SuperArmConstraintSolver import *
from tqdm import tqdm

subcampaign = [0, 1, 2]

min_budget = 0.0
max_budget = 1.0
n_arms = 20
daily_budget = np.linspace(min_budget, max_budget, n_arms)
sigma = 10

T = 60

n_experiments = 100
collected_rewards_per_experiments = []

# print("Starting experiments...")
for e in tqdm(range(0, n_experiments)):
    # Initialize the environment, learner and click for each experiment
    env = []
    gpts_learner = []
    total_clicks_per_t = []
    for s in subcampaign:
        env.append(ClickBudget(s, budgets=daily_budget, sigma=sigma))
        gpts_learner.append(GPTS_Learner(n_arms=n_arms, arms=daily_budget))

    # For each t in the time horizon, run the GP_TS algorithm
    for t in range(0, T):
        total_subcampaign_combination = []
        for s in subcampaign:
            for arm in gpts_learner[s].pull_arm():
                total_subcampaign_combination.append(arm)

        # At the and of the GP_TS algorithm of all the sub campaign , run the Knapsack optimization
        # and save the chosen arm of each sub campaign
        budgets = []
        for n in subcampaign:
            for i in daily_budget:
                budgets.append(i)
        superarm = SuperArmConstraintSolver(total_subcampaign_combination, budgets, max_budget,
                                            n_arms).solve()

        # At the end of each t, save the total click of the arms extracted by the Knapsack optimization
        total_clicks = 0
        for s in subcampaign:
            reward = env[s].round(superarm[s])
            total_clicks += reward
            gpts_learner[s].update(superarm[s], reward)

        total_clicks_per_t.append(total_clicks)

    # At the end of each experiment, save the total click of each t of this experiment
    collected_rewards_per_experiments.append(total_clicks_per_t)
    time.sleep(1)

# Find the optimal value executing the Knapsack optimization on the different environment
# TODO: find the best way to get the optimum value
total_optimal_combination = []
for s in subcampaign:
    for idx in range(0, n_arms):
        total_optimal_combination.append(env[s].means[idx])
optimal_reward = SuperArmConstraintSolver(total_optimal_combination, budgets, max_budget, n_arms).solve()
opt = 0
for s in subcampaign:
    opt += env[s].means[optimal_reward[s]]

print("Opt")
print(opt)
print("Rewards")
print(collected_rewards_per_experiments)
print("Regrets")
print(np.mean(opt - collected_rewards_per_experiments, axis=0))
plt.figure()
plt.ylabel("Regret")
plt.xlabel("t")
plt.plot(np.cumsum(np.mean(opt - collected_rewards_per_experiments, axis=0)), 'g')
plt.legend(["Cumulative Regret"])
plt.show()

plt.figure()
plt.ylabel("Regret")
plt.xlabel("t")
plt.plot((np.mean(opt - collected_rewards_per_experiments, axis=0)), 'r')
plt.legend(["Regret"])
plt.show()
