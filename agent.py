'''
Copyright 2017 Marianne Linhares Monteiro, @mari-linhares at github.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

# for vectors manipulation
import numpy as np

import random

# for copying python objects
import copy

from game import *

LEVEL_OUTPUT = 'agent_training.txt'
THETA_OUTPUT = 'pretrained_agent.npy'


class LinearFunctionSarsaAgent():
    
    def __init__(self, environment, discount_factor=0.2, _lambda=1):

        # pygame environemnt
        self.env = environment

        # we can tune these parameters
        self._lambda = _lambda
        self.number_of_parameters = self.env.bricks_matrix.shape[0] * self.env.bricks_matrix.shape[1] * self.env.number_of_actions
        self.disc_factor = discount_factor
        
        # parameters are initialized randomly
        try:
            self.theta = np.load(THETA_OUTPUT)
            print 'loading %s' % THETA_OUTPUT
        except IOError:
            print 'initializing theta randomly'
            self.theta = np.random.randn(self.number_of_parameters) * 0.1
        
        # eligibility trace
        self.E = self.get_clear_tensor()
    
    def get_clear_tensor(self):
        '''
            Returns a tensor with zeros with the correct shape.
        '''
        return np.zeros(self.number_of_parameters)

    def get_q(self, s, a):
        return np.dot(self.phi(s, a), self.theta)

    def phi(self, s, a):        
        features = np.zeros((self.env.bricks_matrix.shape[0], self.env.bricks_matrix.shape[1], self.env.number_of_actions), dtype=np.int)
        features[:, :, a] = s

        return features.flatten()
   
    def get_alpha(self, s, a):
        return 0.01
       
    def get_e(self, s):
        return 0.1

    def try_all_actions(self, s):
        #print 'state:'
        #print s
        #print 'all actions at this state:'
        #print [np.dot(self.phi(s, a), self.theta) for a in range(self.env.number_of_actions)]
        return [np.dot(self.phi(s, a), self.theta) for a in range(self.env.number_of_actions)]
    
    def get_max_action(self, s):
        return np.max(self.try_all_actions(s))
    
    def choose_random_action(self):
        return np.random.choice(range(self.env.number_of_actions))
 
    def choose_best_action(self, s):
        return np.argmax(self.try_all_actions(s))
    
    def policy(self, s): 
        if random.random() <= self.get_e(s):
            print 'random'
            action = self.choose_random_action()
        else:
            print 'best'
            action = self.choose_best_action(s)

        return action

    def train(self):
        e = 0
        f = open(LEVEL_OUTPUT, 'a+')
        phase = 0
        while 1:
            # clear eligibility trace
            self.E = self.get_clear_tensor()
            # get initial state for current episode
            self.env.next_phase()   
            s = copy.copy(self.env.bricks_matrix)
            # choose a from s with epsilon greedy policy
            a = self.policy(s)
            next_a = a 
                 
            # while game has not ended
            is_s_terminal = False
            phase = 0
            while not is_s_terminal:
                phase += 1
                # execute action
                print 'action: ', a, self.env.actions[a]
                print 'state:'
                print s
                next_s, r = self.env.step(copy.copy(s), a)
              
                # get parameters that represent this state and action
                phi = self.phi(s, a)
                # get q(s, a)
                q = self.get_q(s, a)
                
                if r != -1:
                    # choose next action with epsilon greedy policy
                    next_a = self.policy(next_s)
                    q_next = self.get_q(next_s, next_a)
                    delta = r + q_next - q
                else:
                    delta = r - q 

                self.E += phi
                alpha = self.get_alpha(s, a)
                update_q = alpha * delta * self.E
                self.theta += update_q
                self.E *= (self.disc_factor * self._lambda)
                
                # update state and action
                s = next_s
                a = next_a
                is_s_terminal = (r == -1)
            
            if e % 10 == 0:
                np.save(THETA_OUTPUT, self.theta)                
                print "Episode: %d" % e

            f.write('%d, %d\n' % (e, phase))
            e += 1

        return self.get_value_function()

def main():
    env = Environment(ball_speed=15, state=GameState.AGENT_PLAYING)
    agent = LinearFunctionSarsaAgent(env)
    agent.train()

if __name__ == "__main__":
    main()
