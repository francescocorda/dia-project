import numpy as np
import matplotlib.pyplot as plt
from pythonCode.mab.environment import Environment
from pythonCode.mab.ts_learner import TS_Learner
from pythonCode.mab.greedy_learner import Greedy_Learner


if __name__ == '__main__':

    # define the total number of environments, one environment stands for one subcampaign
    n_environments = 3
    # define the total budget we can allocate to the tree subcampaigns
    budget = 1
    # define the number of points in which we split the range of prices
    number_of_points = 30
    # defines the total number of arms to be by the learners
    n_arms = number_of_points

    # initialize the prices that partitions the budget range
    # Example: [0.  0.03448276 ... 0.96551724  1. ]
    x1 = np.linspace(0, budget, num=n_arms, endpoint=True)
    x2 = np.linspace(0, budget, num=n_arms, endpoint=True)
    x3 = np.linspace(0, budget, num=n_arms, endpoint=True)

    # define 3 functions that simulate the click-per-ad reward of each candidate, since we use Bernoulli distributions
    # these functions must be limited to a max value of 1
    # Example y1:  [0.         0.03448276 ... 0.93103448 0.96551724 1.        ]
    y1 = x1
    # to simulate different possibilities we saturate some curves at a lower value
    y2 = 0.7 * x2
    y3 = 0.3 * x3

    # array used for sliding windows algorithm
    # p1 = np.array([y1[0:4], y1[4:8], y1[8:12], y1[12:16]])
    # p2 = np.array([y2[0:4], y2[4:8], y2[8:12], y2[12:16]])
    # p3 = np.array([y3[0:4], y3[4:8], y3[8:12], y3[12:16]])

    # create numpy array defining the probabilities of getting a reward
    # they're exactly like y1, y2 and y3
    # p1 = np.array(y1)
    # p2 = np.array(y2)
    # p3 = np.array(y3)

    # hardcoded probabilities used to simulate some more irregular environments
    p1 = np.array(np.random.rand(n_arms))
    p2 = np.array(np.random.rand(n_arms))
    p3 = np.array(np.random.rand(n_arms))

    # define the average optimal value that can be obtained for the total number of arms
    # opt = (np.max(p1) + np.max(p2) + np.max(p3)) / 3
    opt = [1, 1, 1]

    # T is the time horizon
    T = 400

    # number of times we repeat the experiment
    n_experiments = 100
    # arrays used to store the rewards obtained by each algorithm
    # Example: [[[0, 0, ... 1, 1],  <- rewards of first environment in first experiment
    #            [0, 0, ... 0, 1],  <- rewards of second environment in first experiment
    #            [0, 0, ... 0, 0]]  <- rewards of third environment in first experiment
    #           ...
    #           [[0, 0, ... 1, 1],  <- rewards of first environment in last experiment
    #            [0, 0, ... 0, 1],  <- rewards of second environment in last experiment
    #            [0, 0, ... 0, 0]]] <- rewards of third environment in last experiment
    #               ^list of experiments of time steps of rewards
    ts_rewards_per_experiment = []
    gr_rewards_per_experiment = []

    # array containing the lists of prices of each subcampaign
    # Example: [array([0.        , 0.03448276, ... 0.96551724, 1.        ]),
    #           array([0.        , 0.03448276, ... 0.96551724, 1.        ]),
    #           array([0.        , 0.03448276, ... 0.96551724, 1.        ])]
    prices = [x1, x2, x3]
    # array containing the lists of probabilities of each subcampaign, corresponds to the click-per-ad
    # conversion probability of each subcampaign
    # Example: [array([0.        , 0.03448276, ... 0.96551724, 1.        ]),
    #           array([0.        , 0.02413793, ... 0.67586207, 0.7       ]),
    #           array([0.        , 0.01034483, ... 0.28965517, 0.3       ])]
    probabilities = [p1, p2, p3]

    # iterate over number of experiments
    for e in range(0, n_experiments):
        # create the environment with all the probabilities associated to each arm for every subcampaign
        # n_arms is an integer indicating the number of possible arms to pull in the environment
        # probabilities is a matrix of float indicating the values of converting click-per-ads
        # in the environment given the corresponding budget
        environment = Environment(n_arms=n_arms, probabilities=probabilities)
        # create the Thompson Sampling Learner. n_environments is an integer. n_arms is an integer.
        # budget is an integer.
        # prices is a matrix n_environments*n_arms (Example: shown above)
        ts_learner = TS_Learner(n_environments=n_environments, n_arms=n_arms, budget=budget, prices=prices)
        # create the Greedy Learner
        gr_learner = Greedy_Learner(n_environments=n_environments, n_arms=n_arms)
        for t in range(0, T):
            # retrieve the arms to pull for each environment (the superarm) from the Thompson Sampling Learner
            pulled_arms = ts_learner.pull_arm()
            # retrieve the reward received from the environment gained from pulling the superarm
            reward = environment.round(pulled_arms)
            # update the parameters of the Thompson Sampling Learner accordingly to the received reward
            ts_learner.update(pulled_arms, reward)

            # retrieve the arms to pull for each environment (the superarm) from the Greedy Learner
            pulled_arms = gr_learner.pull_arm()
            # retrieve the reward received from the environment gained from pulling the superarm
            reward = environment.round(pulled_arms)
            # update the parameters of the Greedy Learner Learner accordingly to the received reward
            gr_learner.update(pulled_arms, reward)
            print('t:' + str(t) + ' exp:' + str(e))

        ts_rewards_per_experiment.append(ts_learner.collected_rewards)
        gr_rewards_per_experiment.append(gr_learner.collected_rewards)

    # list where we store the lists of the mean of the received rewards for each environment
    # Example: TODO
    ts_rewards_history = []
    gr_rewards_history = []

    # list where we store the cumulative sum of rewards of all the experiments previously made for each environment
    ts_cumulative_sum_of_rewards = []
    gr_cumulative_sum_of_rewards = []

    # list where we store the lists of the mean of the cumulated regret for each environment
    ts_regrets_history = []
    gr_regrets_history = []

    # list where we store the regret
    gr_regret = []
    ts_regret = []

    # list where we store the cumulative sum of regrets of all the experiments previously made for each environment
    # ts_cumulative_sum_of_regret = []
    # gr_cumulative_sum_of_regret = []

    for env in range(n_environments):

        # append one list for each environment
        gr_rewards_history.append([])
        ts_rewards_history.append([])

        gr_cumulative_sum_of_rewards.append([])
        ts_cumulative_sum_of_rewards.append([])

        gr_regrets_history.append([])
        ts_regrets_history.append([])

        gr_regret.append([])
        ts_regret.append([])

        for experiment in range(n_experiments):
            # append the rewards of the experiment
            gr_rewards_history[env].append(np.mean(gr_rewards_per_experiment[experiment][env]))
            ts_rewards_history[env].append(np.mean(ts_rewards_per_experiment[experiment][env]))
            gr_regrets_history[env].append(1 - np.mean(gr_rewards_per_experiment[experiment][env]))
            ts_regrets_history[env].append(1 - np.mean(ts_rewards_per_experiment[experiment][env]))

        # compute the cumulative sum for each environment
        gr_cumulative_sum_of_rewards[env] = np.cumsum(gr_rewards_history[env])
        ts_cumulative_sum_of_rewards[env] = np.cumsum(ts_rewards_history[env])

        # compute the regret for each environment
        gr_regret[env] = np.cumsum(gr_regrets_history[env])
        ts_regret[env] = np.cumsum(ts_regrets_history[env])

        # plot the graphs
        plt.figure(env)
        plt.ylabel("Regret Env" + str(env))
        plt.xlabel("t")
        plt.plot(range(n_experiments), ts_regret[env], 'r')
        plt.plot(range(n_experiments), gr_regret[env], 'g')
        plt.legend(["TS", "Greedy"])

    plt.show()