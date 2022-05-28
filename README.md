# R-Max-Agent

This agent is a curious agent, who acts well in a deterministic environment when the probabilities of each move are unknown. This agent is divided into 2 main parts:
# The Learner
The agent learns the policy by randomly trying moves, and testing what their effect is. He saves the result and calculates the odds after each turn.
Let us note that after performing about 100 moves of a certain type (and even much less, but 100 moves guarantee this with a high probability) it will reach approximately > 95% of the true probability of the effects of a move.

# The Executor
The executor: The agent uses the Policy created by the learner, he checks every round all the legal moves: For each move - he checks what the chances are that he will get him to a new place, and will make the move that will make him get to a new place with the highest chance (curiosity policy ). If there is no such - will choose at random.
