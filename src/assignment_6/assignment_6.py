import os

import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import pandas as pd

from src.assignment_2.gpts_learner import GPTSLearner
from src.utils.constants import img_path
from src.utils.knapsack import Knapsack
from src.assignment_6.weighted_ts_learner import WeightedTSLearner
from src.assignment_4.pricing_env import PricingEnv as PricingEnvironment
from src.assignment_2.click_env import ClickEnv
from scipy import interpolate

# number of timesteps
T = 365
colors = ['r', 'b', 'g']

# number of experiments
n_experiments = 50

# subcampaigns array
subcampaigns = [0, 1, 2]
# probabilities of a user to correspond to each class
user_classes_probabilities_vector = [1 / 4, 1 / 2, 1 / 4]

# minimum and maximum value for the advertising
min_value_advertising = 0.0
max_value_advertising = 1.0
# sigma value for the variance of the number of clicks
sigma_advertising = 1

# minimum and maximum value for the pricing
min_value_pricing = 0.0
max_value_pricing = 100.0

readFile = '../data/pricing.csv'

# Read environment data from csv file
data = pd.read_csv(readFile)
n_arms_pricing = int(np.ceil(np.power(np.log2(T) * T, 1 / 4)))
print(n_arms_pricing)

y_values_pricing = []
# The values of the y for each function
for i in range(0, len(data.index)):
    y_values_pricing.append(np.array(data.iloc[i]))

x_values_pricing = [np.linspace(min_value_pricing, max_value_pricing, len(y_values_pricing[0])) for i in
                    range(0, len(subcampaigns))]

data = pd.read_csv('../data/click_env.csv')
n_arms_advertising = 21
# array of budgets spacing from min_value_advertising to max_value_advertising
daily_budgets = np.linspace(min_value_advertising, max_value_advertising, n_arms_advertising)

y_values_advertising = []
# The values of the y for each function
for i in range(0, len(data.index)):
    y_values_advertising.append(np.array(data.iloc[i]))
x_values_advertising = [np.linspace(min_value_advertising, max_value_advertising, len(y_values_advertising[0])) for a in
                        range(0, len(subcampaigns))]

demand_probabilities = [interpolate.interp1d(x_values_pricing[subcampaign], y_values_pricing[subcampaign])
                        for subcampaign in range(len(subcampaigns))]
# array of prices spacing from min_value_pricing to max_value_pricing
conversion_prices = np.linspace(min_value_pricing, max_value_pricing, n_arms_pricing)

# collects the rewards for each experiment for the pricing task executed by the Thompson Sampling algorithm
ts_rewards_per_experiment_pricing = []
# collects the rewards for each experiment for the advertising task executed by the Gaussian Processes algorithm
gp_rewards_per_experiment_advertising = []

# arrays to store the environments for each task
environments_pricing = []
environments_advertising = []

# arrays to store the learners
advanced_ts_learners_pricing = []
gpts_learner_advertising = []

# initialization of the arrays of the rewards and of the environments
for s in subcampaigns:
    ts_rewards_per_experiment_pricing.append([])
    environments_pricing.append(PricingEnvironment(n_arms=n_arms_pricing,
                                                   conversion_rates=demand_probabilities[s](conversion_prices)))
    environments_advertising.append(
        ClickEnv(daily_budgets, sigma_advertising, x_values_advertising[s], y_values_advertising[s], s + 1, colors[s]))

for e in range(0, n_experiments):

    # reinitialization of learners arrays for a new experiment
    advanced_ts_learners_pricing = []
    gpts_learner_advertising = []

    # memory of accumulated revenue in each timestep
    total_revenue_per_t = []

    # initialization of learners and tuning of gaussian process hyperparameters
    for s in subcampaigns:
        advanced_ts_learners_pricing.append(WeightedTSLearner(n_arms=n_arms_pricing, prices=conversion_prices))
        gpts_learner_advertising.append(GPTSLearner(n_arms=n_arms_advertising, arms=daily_budgets))

        # Learning of hyper parameters before starting the algorithm
        new_x = []
        new_y = []
        for i in range(0, 100):
            new_x.append(np.random.choice(daily_budgets, 1))
            new_y.append(environments_advertising[s].round(np.where(daily_budgets == new_x[i])))
        gpts_learner_advertising[s].generate_gaussian_process(new_x, new_y)

    # experiment start
    description = 'Experiment ' + str(e + 1) + ' - Time processed'
    for t in tqdm(range(0, T), desc=description, unit='t'):

        # arrays to store the combinations of possible values
        values_combination_of_each_subcampaign = []
        best_price_list = []
        conversion_rate_list = []
        price_index_list = []

        # Thompson Sampling and GP-TS Learner
        for s in subcampaigns:
            # thompson sampling
            # the learner pulls the best arm according to its estimation, the pulled arm returns the index of the
            # according chosen price and the estimated conversion rate of the arm
            price_index, conversion_rate = advanced_ts_learners_pricing[s].pull_arm()
            # this function retrieves the price corresponding to the pulled index
            proposed_price = advanced_ts_learners_pricing[s].prices[price_index]
            # saving of the price indexes
            price_index_list.append(price_index)
            # saving of the conversion rates
            conversion_rate_list.append(conversion_rate)
            # saving of the corresponding prices
            best_price_list.append(proposed_price)
            # extraction of the real price from the environment
            reward_pricing = environments_pricing[s].round(price_index)
            # update of the estimation values of the environment
            advanced_ts_learners_pricing[s].update(price_index, reward_pricing * proposed_price)

            # advertising
            # the learner returns the entire array of the expected number of clicks for each possible arm
            click_numbers_vector = np.array(gpts_learner_advertising[s].pull_arm())
            # the number of clicks gets multiplied by the conversion rates in order to estimate how many users would
            # actually buy the product
            modified_rewards = click_numbers_vector * proposed_price * conversion_rate \
                                                    * user_classes_probabilities_vector[s]
            # the modified rewards are stored in a list
            values_combination_of_each_subcampaign.append(modified_rewards.tolist())

        # At the and of the GP_TS algorithm of all the sub campaign, run the Knapsack optimization
        # and save the chosen arm of each sub campaign

        superarm = Knapsack(values_combination_of_each_subcampaign, daily_budgets).solve()

        # At the end of each t, save the total click of the arms extracted by the Knapsack optimization
        total_revenue = 0
        for s in subcampaigns:
            # retrieve the reward in number of click collected from each subcampaign
            reward_advertising = environments_advertising[s].round(superarm[s])
            # retrieve the conversion rate for that specific
            conversion = environments_pricing[s].conversion_rates[price_index_list[s]]
            # compute the total outcome collected from the procedure
            total_revenue += reward_advertising * best_price_list[s] * conversion * user_classes_probabilities_vector[s]
            # update the learner
            gpts_learner_advertising[s].update(superarm[s], reward_advertising)

        # store the collected revenue
        total_revenue_per_t.append(total_revenue)

    # store the collected rewards for each experiment
    for s in subcampaigns:
        ts_rewards_per_experiment_pricing[s].append(advanced_ts_learners_pricing[s].collected_rewards)

    gp_rewards_per_experiment_advertising.append(total_revenue_per_t)

# Find the optimal value executing the Knapsack optimization on the different environments

total_optimal_combination = []
conversion_rate_list = []
best_price_list = []

for s in subcampaigns:
    # factor by which we weight the advertising budget curve == price*conversion_rate
    weighting_factor_of_subcampaign_list = []
    # iterate all the possible prices
    for conversion_rate_index in range(n_arms_pricing):
        # retrieve the actual price
        price = advanced_ts_learners_pricing[s].prices[conversion_rate_index]
        # retrieve the actual conversion rate
        conversion_rate = environments_pricing[s].conversion_rates[conversion_rate_index]
        # compute the weighting factor
        weighting_factor_of_subcampaign_list.append(price * conversion_rate * user_classes_probabilities_vector[s])

    # extract the best combination of price and conversion rate
    best_weighting_factor = max(weighting_factor_of_subcampaign_list)
    # retrieve the index of the weighting factor
    best_weighting_factor_index = weighting_factor_of_subcampaign_list.index(best_weighting_factor)
    # retrieve best conversion rate
    best_conversion_rate = environments_pricing[s].conversion_rates[best_weighting_factor_index]

    # store all the conversion rate for each subcampaign
    conversion_rate_list.append(best_conversion_rate)
    # retrieve the best price corresponding to the best conversion rate
    best_price = advanced_ts_learners_pricing[s].prices[best_weighting_factor_index]
    # store all the conversion rate for each subcampaign
    best_price_list.append(best_price)

    # retrieve the number clicks returned by each subcampaign
    click_numbers_vector = np.array(environments_advertising[s].means)
    # compute the rewards
    modified_rewards = click_numbers_vector * best_weighting_factor
    # build the combination vector corresponding of the collection of modified rewards for each subcampaign
    total_optimal_combination.append(modified_rewards)

# solve the Knapsack problem
optimal_reward = Knapsack(total_optimal_combination, daily_budgets).solve()

# initialize the optimal advertising variable
opt_advertising = 0

# retrieve the optimal values for each subcampaign and compute the optimal outcome
for s in subcampaigns:
    opt_advertising += environments_advertising[s].means[optimal_reward[s]] \
                       * conversion_rate_list[s] * best_price_list[s] \
                       * user_classes_probabilities_vector[s]

# plot the graphs
np.set_printoptions(precision=3)
print("Opt")
print(opt_advertising)
print("Rewards")
print(gp_rewards_per_experiment_advertising)
print("Regrets")
regrets = np.mean(np.array(opt_advertising) - gp_rewards_per_experiment_advertising, axis=0)
print(regrets)
plt.figure()
plt.ylabel("Regret")
plt.xlabel("t")
plt.plot(np.cumsum(np.mean(np.array(opt_advertising) - gp_rewards_per_experiment_advertising, axis=0)), 'g')
plt.legend(["Cumulative Regret"])
img_name = "assignment_6_cum_regret.png"
plt.savefig(os.path.join(img_path, img_name))
plt.show()

plt.figure()
plt.ylabel("Reward")
plt.xlabel("t")
plt.axhline(y=opt_advertising, color='black', linestyle='dashed')
plt.plot(np.mean(gp_rewards_per_experiment_advertising, axis=0), 'r')
plt.legend(["Optimal Reward", "Instantaneous Reward"])
img_name = "assignment_6_inst_reward.png"
plt.savefig(os.path.join(img_path, img_name))
plt.show()
