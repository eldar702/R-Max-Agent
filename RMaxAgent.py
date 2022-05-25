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
LAST_STATE = None
LAST_ACTION = None

#########################################################################################################
###########################            R-MAX Agent Class              #############################
#########################################################################################################

class RMaxAgent(Executor):
    ##########################             Init Functions               #################################
    def __init__(self):
        super(RMaxAgent, self).__init__()
        self.epsilon = 1
        #self.actions_list, self.states_list, self.actions_idx, self.states_idx = [], [], {}, {}
        self.action_options = ["south", "north", "west", "east"]
        self.actions_options_dict, self.actions_count_dict = {}, {}

    def initialize(self, services):
        self.services = services
        self.initialize_Q_table()

    def init_actions_counting(self):
        for action in self.services.valid_actions.provider.parser.actions:
            if action != "pick-food":
                self.actions_happened_dict[action] = 0

        for action in self.actions_happened_dict.keys():
            if self.is_probabilistic(action):
                pre_conditions = self.services.valid_actions.provider.parser.actions[action].precondition
                for pre_cond in pre_conditions:
                    if pre_cond.name in self.action_options:
                        self.action_to_result_dict[pre_cond.name] = 0
                self.action_to_result_dict[action] = pre_conditions_dict

    # check with the pddl parser if its probabilistic action or deterministic
    def is_probabilistic(self, action):
        return hasattr(self.services.valid_actions.provider.parser.actions[action], "prob_list")

    def next_action(self):
        global LAST_ACTION, LAST_STATE
        chosen_action = None
        self.update_Q_table()
        self.write_Q_table()


        ##############################             PDDL  Methods               #################################
    def get_agent_location(self):
        state = self.services.perception.get_state()
        agent_place = list(state["at"])
        agent_place = agent_place[0][1]
        return agent_place

    #######################             R-Max  TABLE  Methods               ################################

    ####################             R-MAX - LEARNING  Methods               #############################

    ##############################             PDDL  Methods               #################################
    def get_agent_location(self):
        state = self.services.perception.get_state()
        agent_place = list(state["at"])
        agent_place = agent_place[0][1]
        return agent_place

##############################             HELPER's  Methods               #################################
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
