import random
import sys
import numpy as np
import os.path
##############################            Imports & Globals              #################################
from pddlsim.executors.executor import Executor
from pddlsim.local_simulator import LocalSimulator

# read files:
input_flag = sys.argv[1]
domain_path = sys.argv[2]
problem_path = sys.argv[3]
policy_file_path = sys.argv[4]

# GLOBAL's
CURRENT_STATE = None
LAST_STATE = None
LAST_ACTION = None
COUNTER = 0
#########################################################################################################
###########################            R-MAX Agent Class              #############################
#########################################################################################################

class RMaxAgent(Executor):
    ##########################             Init Functions               #################################
    def __init__(self):
        super(RMaxAgent, self).__init__()


        #self.actions_list, self.states_list, self.actions_idx, self.states_idx = [], [], {}, {}
        self.action_options = ["south", "north", "west", "east"]
        self.actions_options_dict, self.actions_count_dict, self.topologic_graph = {}, {}, {}

    def initialize(self, services):
        self.services = services
        self.init_RMax_dict()
        self.create_topologic_graph()
        pass

    ##########################              Run Agent Run!                  #################################
    def next_action(self):
        global LAST_ACTION, LAST_STATE, COUNTER, CURRENT_STATE
        chosen_action = None
        CURRENT_STATE = self.services.perception.get_state()
        self.update_RMax_dict()
        self.update_RMax_file()

        valid_actions = self.services.valid_actions.get()
        if len(valid_actions) == 0:
            chosen_action = None
        elif len(valid_actions) == 1:
            chosen_action = valid_actions[0]
        else:
            chosen_action = random.choice(valid_actions)
        LAST_STATE = self.services.perception.get_state()
        LAST_ACTION = chosen_action.split()[0].split('(')[1]

        return chosen_action

    #######################             R-Max  TABLE  Methods               ################################
    def init_RMax_dict(self):
        for action in self.services.valid_actions.provider.parser.actions:
            if action != "pick-food":
                self.actions_count_dict[action] = 0
        for action in self.actions_count_dict.keys():
            if self.is_probabilistic(action):
                temp_dict = {}
                conditions = self.services.valid_actions.provider.parser.actions[action].precondition
                for condition in conditions:
                    if condition.name in self.action_options:
                        temp_dict[condition.name] = 0
                if len(self.services.valid_actions.provider.parser.actions[action].prob_list) != len(temp_dict.keys()):
                    temp_dict["stay-in-place"] = 0
                self.actions_options_dict[action] = temp_dict
        pass

    def update_RMax_dict(self):

        global LAST_ACTION, LAST_STATE, CURRENT_STATE
        if LAST_ACTION is None:
            return

        current_state = list(CURRENT_STATE['at'])[0][1]
        last_state = list(LAST_STATE['at'])[0][1]

        action = self.get_action_which_actually_happened( (current_state, last_state) )
        self.actions_count_dict[last_state] += 1
        self.actions_options_dict[last_state][action] += 1
        



    def update_RMax_file(self):
        new_dict = {}
        for action in self.actions_count_dict.keys():
            action_probability = 0
            denominator = self.actions_count_dict[action]
            
            new_dict[action] = actions_probability
        f = open(policy_file_path, 'w')
        f.write(str(new_dict))
        f.close()
        pass
    ####################             R-MAX - LEARNING  Methods               #############################

    ##############################             PDDL  Methods               #################################
    def get_agent_location(self):
        state = self.services.perception.get_state()
        agent_place = list(state["at"])
        agent_place = agent_place[0][1]
        return agent_place

    # check with the pddl parser if its probabilistic action or deterministic
    def is_probabilistic(self, action):
        return hasattr(self.services.valid_actions.provider.parser.actions[action], "prob_list")

    def get_action_which_actually_happened(self, tuple_state):
        global LAST_STATE, LAST_ACTION
        happened_act = None
        if tuple_state[0] == tuple_state[1]:
            return "stay-in-place"
        for direction in self.topologic_graph:
            for checked_tuple in direction:
                if checked_tuple == tuple_state:
                    return direction
                
        return happened_act


##############################             HELPER's  Methods               #################################

    def create_topologic_graph(self):
        for name_of_action in self.services.parser.initial_state:
            if name_of_action in self.action_options:
                self.topologic_graph[name_of_action] = self.services.parser.initial_state[name_of_action]

def save_dict_to_file(dic):
    f = open(policy_file_path,'w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open(policy_file_path,'r')
    data = f.read()
    f.close()
    return eval(data)

if input_flag == "-L":
    print LocalSimulator().run(domain_path, problem_path, RMaxAgent())

# elif input_flag == "-E":
#     print LocalSimulator().run(domain_path, problem_path, CuriousAgent())
