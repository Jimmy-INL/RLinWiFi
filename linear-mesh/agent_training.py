
#%%
from ns3gym import ns3env
from comet_ml import Experiment, Optimizer
import tqdm
import subprocess
from collections import deque
import numpy as np

from agents.ddpg.agent import Agent, Config
# from agents.dqn.agent import Agent, Config
# from agents.dqn.model import QNetworkTf
from agents.teacher import Teacher, EnvWrapper

#%% [markdown]
# ### Basic constants and setting up environment

#%%
scenario = "convergence"

simTime = 10 # seconds
stepTime = 0.01  # seconds
history_length = 10


EPISODE_COUNT = 20
steps_per_ep = int(simTime/stepTime)

sim_args = {
    "simTime": simTime,
    "envStepTime": stepTime,
    "historyLength": 10,
    "agentType": Agent.TYPE,
    "nonZeroStart": True,
    "scenario": "convergence",
    "nWifi": 7
}
print("Steps per episode:", steps_per_ep)

threads_no = 1
env = EnvWrapper(threads_no, **sim_args)


#%%
# config = Config(buffer_size=2e3, batch_size=64, gamma=0.99, tau=1e-3, lr=5e-4)
config = Config(buffer_size=1.5e4*threads_no, batch_size=512, gamma=0.99, tau=1e-3, lr_actor=6e-5, lr_critic=1e-3)


#%%
env.reset()
ob_space = env.observation_space
ac_space = env.action_space

print("Observation space shape:", ob_space)
print("Action space shape:", ac_space)

assert ob_space is not None

#%% [markdown]
# ### Creating and training agent

#%%
# import tensorflow as tf

# class Network(QNetworkTf):
#     def _inference(self):
#         with tf.variable_scope("inference_"+self.name):
#             layer = tf.layers.dense(self.input, 128, activation=tf.nn.relu)
# #             layer = tf.layers.dense(layer, 128, activation=tf.nn.relu)
# #             layer = tf.layers.batch_normalization(layer)
#             layer = tf.layers.dense(layer, 64, activation=tf.nn.relu)
#             layer = tf.layers.dense(layer, 32, activation=tf.nn.relu)
# #             layer = tf.layers.dense(layer, 256, activation=tf.nn.relu)
# #             layer = tf.layers.dense(layer, 64, activation=tf.nn.relu)
#             layer = tf.layers.dense(layer, self.action_size)
#         return layer


#%%
optimizer = Optimizer("OZwyhJHyqzPZgHEpDFL1zxhyI")
  # Declare your hyper-parameters:
# actor_fc1 integer [1, 4] [2]
# actor_fc2 integer [1, 4] [2]
# actor_fc3 integer [1, 4] [2]

# critic_fc1 integer [1, 4] [2]
# critic_fc2 integer [1, 4] [2]
# critic_fc3 integer [1, 4] [2]

params = """
lr_actor real [1e-6, 1e-4] [6e-5] log
lr_critic real [1e-5, 1e-3] [8e-4] log
"""
optimizer.set_params(params)

teacher = Teacher(env, 1)

# agent = Agent(Network, history_length, action_size=3, config=config)
# agent.set_epsilon(0.9, 0.01, 25)
# teacher.train(EPISODE_COUNT, simTime, stepTime, "Inp: window Mb sent", "Rew: normalized speed", "DQN", "Convergence", "Instances: 2", "Net: 128, 64, 32")

while True:
    # Get a suggestion
    suggestion = optimizer.get_suggestion()
    config = Config(buffer_size=1.5e3*threads_no, batch_size=512, gamma=0.99, tau=1e-3, lr_actor=suggestion["lr_actor"], lr_critic=suggestion["lr_critic"])
    
#     actor_l = [2**(suggestion["actor_fc1"]+5), 2**(suggestion["actor_fc2"]+4), 2**(suggestion["actor_fc3"]+3)]
#     critic_l = [2**(suggestion["critic_fc1"]+5), 2**(suggestion["critic_fc2"]+4), 2**(suggestion["critic_fc3"]+3)]
    actor_l = [128, 64, 32]
    critic_l = [512, 256, 64]
    print("Params:")
    for k, v in suggestion.params.items():
        print(f"{k}: {v}")
    
    agent = Agent(history_length, action_size=1, config=config, actor_layers = actor_l, critic_layers = critic_l)

    # Test the model
    logger = teacher.train(agent, EPISODE_COUNT, simTime, stepTime, "Inp: collisions mb", "Rew: normalized speed", "DDPG", "Convergence", f"Actor: {actor_l}", f"Critic: {critic_l}", f"Instances: {threads_no}",
                          **config.__dict__)
    
    # Report the score back
    suggestion.report_score("last_speed", logger.last_speed)
    del agent


SCRIPT_RUNNING = False


#%%
config.__dict__


