import datetime

import numpy as np
import tqdm

import atari
import dq_learner
import atari_dqn
import coin_game

num_steps = 50000000
test_interval = 250000
test_frames = 125000

game = 'coin_game'
game_dir = './roms'
results_dir = './results/double_dqn/coin_game'

# open results file
results_fn = '%s/%s_results.txt' % (results_dir, game)
results_file = open(results_fn, 'w')


def evaluate_agent_reward(steps, env, agent, epsilon):
    env.terminate_on_end_life = False
    env.reset_environment()
    total_reward = 0
    episode_rewards = []
    for i in tqdm.tqdm(range(steps)):
        if env.is_current_state_terminal():
            episode_rewards.append(total_reward)
            total_reward = 0
            env.reset_environment()
        state = env.get_current_state()
        if np.random.uniform(0, 1) < epsilon:
            action = np.random.choice(env.get_actions_for_state(state))
        else:
            action = agent.get_action(state)

        state, action, reward, next_state, is_terminal = env.perform_action(action)
        total_reward += reward
    if not episode_rewards:
        episode_rewards.append(total_reward)
    return episode_rewards


def train(agent, env, test_epsilon):
    step_num = 0
    steps_until_test = test_interval
    best_eval_reward = - float('inf')
    while step_num < num_steps:
        env.reset_environment()
        env.terminate_on_end_life = True
        start_time = datetime.datetime.now()
        episode_steps, episode_reward = agent.run_learning_episode(env)
        end_time = datetime.datetime.now()
        step_num += episode_steps
        print 'Steps:', step_num, '\tEpisode Reward:', episode_reward, '\tSteps/sec:', episode_steps / (
        end_time - start_time).total_seconds(), '\tEps:', agent.epsilon

        steps_until_test -= episode_steps
        if steps_until_test <= 0:
            steps_until_test += test_interval
            print 'Evaluating network...'
            episode_rewards = evaluate_agent_reward(test_frames, env, agent, test_epsilon)
            mean_reward = np.mean(episode_rewards)

            if mean_reward > best_eval_reward:
                best_eval_reward = mean_reward
                agent.save_network('%s/%s_best_net.ckpt' % (results_dir, game))

            print 'Mean Reward:', mean_reward, 'Best:', best_eval_reward
            results_file.write('Step: %d -- Mean reward: %.2f\n' % (step_num, mean_reward))
            results_file.flush()


def train_dqn(env, num_actions):
    training_epsilon = 0.1
    test_epsilon = 0.05

    dqn = atari_dqn.AtariDQN(4, num_actions, shared_bias=False)
    agent = dq_learner.DQLearner(dqn, num_actions, target_copy_freq=10000, epsilon_end=training_epsilon, double=False)

    train(agent, env, test_epsilon)


def train_double_dqn(env, num_actions):
    training_epsilon = 0.01
    test_epsilon = 0.001

    dqn = atari_dqn.AtariDQN(4, num_actions)
    agent = dq_learner.DQLearner(dqn, num_actions, epsilon_end=training_epsilon)

    train(agent, env, test_epsilon)

def setup_atari_env():
    # create Atari environment
    env = atari.AtariEnvironment(game_dir + '/' + game + '.bin')
    num_actions = len(env.ale.getMinimalActionSet())
    return env, num_actions

def setup_coin_env():
    env = coin_game.CoinGame()
    num_actions = 4
    return env, num_actions

train_dqn(*setup_coin_env())
#train_double_dqn(*setup_coin_env())
