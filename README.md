# Introduction

# Pseudocode
```
Class HMM(init,emit,trans,obs):
  __init__:
    observation = "string"
    initial probabilities = {state:np.log(prob) for state:prob in init}
    emission probabilities = {state:np.log(prob) for state:prob in emit}
    transition probabilities = {state:np.log(prob) for state:prob in trans}
    score_matrix = []
    traceback_matrix = []

    if sum(init.values()) != 1
      raise error
    if sum(emit.values()) != 1
      raise error
    if sum(trans.values()) != 1
      raise error
    if set(observation) not in obs
      raise error
    
  self.initialize_matrix(length, width):
    score_matrix = np.zeros()
    traceback_matrix = np.zeros()

  self.update_matrix(x,y,value,traceback):
    score_matrix[x,y] = value
    traceback_matrix[x,y] = traceback

  self.traceback():
    path = 
    return path[::-1]

  self.viterbi_algorithm():
    self.initialize_matrix(n,n)
    for initial_prob in initaial probabilities:
      score = max(initial_prob * emission_prob)
      direction = state_initial
      self.update_matrix(index(initial_prob),0, score, direction)

    for i in range(1:len(inside_list)):
      score = max(trans_prob * emission_prob)
      direction = current_state
      self.update_matrix(i, (integer based on number of states), score, direction)

    best_score = max(score_matrix[last column])
    best_column = index of best_score in score_matrix
    traceback_path = self.traceback(traceback_matrix, best_column)

    return traceback_path, best_score
```

# Results


# Successes


# Struggles


# Reflection and Adaptive Learning

# Personal Reflection
## Member

## Member


## Member


# Generative AI Appendix
