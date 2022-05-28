
##############################            Imports & Globals              #################################
import random
import sys
import time
from copy import deepcopy
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
TIMER = time.time()
COUNTER = 0
#########################################################################################################
###########################            R-MAX Agent Class              #############################
#########################################################################################################

class RMaxLearningAgent(Executor):
    ##########################             Init Functions               #################################
    def __init__(self):
        super(RMaxLearningAgent, self).__init__()

        #self.actions_list, self.states_list, self.actions_idx, self.states_idx = [], [], {}, {}
        self.action_options = ["south", "north", "west", "east"]
        self.actions_options_dict, self.actions_count_dict, self.topologic_graph, self.actions_probability = {}, {}, {}, {}

    def initialize(self, services):
        self.services = services
        self.init_RMax_dict()
        self.create_topologic_graph()
        pass

    ##########################              Run Agent Run!                  #################################
    def next_action(self):
        global LAST_ACTION, LAST_STATE, CURRENT_STATE
        if self.services.goal_tracking.reached_all_goals() and minute_passed(0.5):
            return None

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

        self.actions_probability = deepcopy(self.actions_options_dict)
        pass

    def update_RMax_dict(self):

        global LAST_ACTION, LAST_STATE, CURRENT_STATE
        if LAST_ACTION is None:
            return

        current_state = list(CURRENT_STATE['at'])[0][1]
        last_state = list(LAST_STATE['at'])[0][1]

        action = self.get_action_which_actually_happened( (last_state, current_state) )
        if action == "pick-food" or LAST_ACTION == "pick-food": return
        self.actions_count_dict[LAST_ACTION] += 1
        self.actions_options_dict[LAST_ACTION][action] += 1
        pass

    def update_RMax_file(self):
        self.update_probabilities()
        f = open(policy_file_path, 'w')
        f.write(str(self.actions_probability))
        f.close()

    ####################             R-MAX - LEARNING  Methods               #############################
    def update_probabilities(self):
        for action in self.actions_options_dict.items():
            checked_action = action[0]
            for checked_direction in action[1]:
                numerator = self.actions_options_dict[checked_action][checked_direction]
                denominator = self.actions_count_dict[checked_action]
                action_probability = division_Action( numerator, denominator)
                self.actions_probability[checked_action][checked_direction] = action_probability
        pass
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

        if tuple_state[0] == tuple_state[1]:
            return "stay-in-place"
        for direction_topologic in self.topologic_graph.items():
            for checked_tuple in direction_topologic[1]:
                if checked_tuple == tuple_state:
                    return direction_topologic[0]
##############################             HELPER's  Methods               #################################

    def create_topologic_graph(self):
        for name_of_action in self.services.parser.initial_state:
            if name_of_action in self.action_options:
                self.topologic_graph[name_of_action] = self.services.parser.initial_state[name_of_action]

#########################################################################################################
###########################            QExecutorAgent Class              #############################
#########################################################################################################
class RMaxAgent(RMaxLearningAgent):
    ##########################             Init Functions               #################################
    def __init__(self):
        super(RMaxAgent, self).__init__()
        self.nodes_visited_boolean = {}
        self.most_curiosity_prob, self.most_curiosity_action = float("-inf"), None
    def initialize(self, services):
        self.services = services
        self.create_topologic_graph()
        self.create_nodes_list()
        self.actions_probability = load_dict_from_file()


    def next_action(self):
        if self.services.goal_tracking.reached_all_goals():
            return None

        valid_actions = self.services.valid_actions.get()
        agent_location = self.get_agent_location()
        self.nodes_visited_boolean[agent_location] = True
        if len(valid_actions) == 0:
            return None
        if len(valid_actions) == 1:
            return valid_actions[0]

        else:
            self.most_curiosity_action, self.most_curiosity_prob = None, float("-inf")
            for checked_act in valid_actions:
                if "food" in checked_act: return checked_act
                checked_action = checked_act.replace('(', "")
                checked_action = checked_action.replace(')', "")
                splited_action = checked_action.split()
                action_kind, agent_place, to_where1 = splited_action[0], splited_action[2], splited_action[3]
                self.check_who_is_bigger(checked_act, action_kind, to_where1)
                if len(splited_action) >= 5:  # check if is a prob act with different end states (except the same place)
                    to_where2 = splited_action[4]
                    self.check_who_is_bigger(checked_act, action_kind, to_where2, False)
            if self.most_curiosity_action is None:
                return random.choice(valid_actions)

            return self.most_curiosity_action

    def check_who_is_bigger(self, checked_act, action_kind, place, is_major=True):
        if not self.nodes_visited_boolean[place]:
            checked_prob = self.what_the_probability(action_kind, is_major)
            if checked_prob > self.most_curiosity_prob:
                self.most_curiosity_prob = checked_prob
                self.most_curiosity_action = checked_act

    def what_the_probability(self, action_kind, is_major):
        direction = check_direction(action_kind)
        probability = self.actions_probability[action_kind][direction]
        if is_major:
            return probability
        else:
            return 1 - probability


    def create_nodes_list(self):
        for direction in self.topologic_graph.items():
            for checked_tuple in direction[1]:
                for state in checked_tuple:
                    if state not in self.nodes_visited_boolean:
                        self.nodes_visited_boolean[state] = False

##########################                Helper Functions                  ###############################
def save_dict_to_file(dic):
    f = open(policy_file_path,'w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open(policy_file_path,'r')
    data = f.read()
    f.close()
    return eval(data)

def minute_passed( minutes_number):
    return time.time() - TIMER >= (60 * minutes_number)


def division_Action(numerator, denominator):
    if denominator == 0:
        return 0
    return float("{:.3f}".format(float(numerator) / float(denominator)))

def check_direction(action):
    for direction in ["west", "east", "south", "north"]:
        if direction in action: return direction
    return None


#############################              Start Flags              ###################################
if input_flag == "-L":
    print LocalSimulator().run(domain_path, problem_path, RMaxLearningAgent())

elif input_flag == "-E":
    print LocalSimulator().run(domain_path, problem_path, RMaxAgent())
