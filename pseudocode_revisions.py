Class HMM(init_probs, trans_probs, emit_probs):
  # The model holds the three dictionaries only.
  # The observation sequence is passed to viterbi_algorithm, so one model can decode many sequences.

  __init__(init_probs, trans_probs, emit_probs):
    # Step 1. store the raw inputs (needed for the checks)
    self.init_probs  = init_probs
    self.trans_probs = trans_probs
    self.emit_probs  = emit_probs

    # Step 2. derive states and alphabet from the dictionaries (never hard-coded)
    self.states      = list(init_probs.keys())                     # fixed order, i.e. ['I', 'G']
    self.state_index = {state: row for row, state in enumerate(self.states)}   # i.e. {'I': 0, 'G': 1}
    self.alphabet    = set(emit_probs[self.states[0]].keys())      # i.e. {'A', 'C', 'G', 'T'}

    # Step 3. validate the RAW probabilities, before logs (log values no longer sum to 1)
    self.validate()

    # Step 4. convert to log space once (Durbin p. 78); trans and emit are NESTED dictionaries
    self.log_init  = {state: np.log(p) for state, p in init_probs.items()}
    self.log_trans = {from_state: {to_state: np.log(p) for to_state, p in row.items()}
                      for from_state, row in trans_probs.items()}
    self.log_emit  = {state: {symbol: np.log(p) for symbol, p in row.items()}
                      for state, row in emit_probs.items()}
    # OPEN DECISION: zero probabilities -> allow -inf, or pseudocounts?

    self.score_matrix     = None    # built in initialize_matrix(), filled in viterbi_algorithm()
    self.traceback_matrix = None

  validate():
    state_set = set(self.states)
    if set(trans_probs.keys()) != state_set: raise ValueError
    for from_state, row in trans_probs.items():
      if set(row.keys()) != state_set: raise ValueError
    if set(emit_probs.keys()) != state_set: raise ValueError
    for state, row in emit_probs.items():
      if set(row.keys()) != alphabet: raise ValueError
    if any probability in init/trans/emit < 0: raise ValueError
    if not np.isclose(sum(init_probs.values()), 1): raise ValueError     # tolerance, not != 1
    for each row in trans_probs:
      if not np.isclose(sum(row.values()), 1): raise ValueError           # check EACH row
    for each row in emit_probs:
      if not np.isclose(sum(row.values()), 1): raise ValueError

  check_observations(observations):
    if len(observations) == 0: raise ValueError
    unknown_symbols = set(observations) - self.alphabet      # subset check, not "equals"
    if unknown_symbols: raise ValueError naming unknown_symbols

  initialize_matrix(num_states, num_positions):
    self.score_matrix     = np.full((num_states, num_positions), -np.inf)
    self.traceback_matrix = np.full((num_states, num_positions), -1, dtype=int)

  update_matrix(row, column, score, previous_row):
    self.score_matrix[row, column]     = score
    self.traceback_matrix[row, column] = previous_row

  traceback(best_final_row):
    path_rows = [best_final_row]
    last_column = self.traceback_matrix.shape[1] - 1
    for column in range(last_column, 0, -1):          # column 0 has no pointer
      previous_row = self.traceback_matrix[path_rows[-1], column]
      path_rows.append(previous_row)
    path_rows.reverse()
    return [self.states[row] for row in path_rows]

  viterbi_algorithm(observations):
    self.check_observations(observations)
    num_states    = len(self.states)
    num_positions = len(observations)
    self.initialize_matrix(num_states, num_positions)

    # STEP 1: first column. No max, no pointer (Durbin p. 56; primer Step 1)
    first_symbol = observations[0]
    for state in self.states:
      score = self.log_init[state] + self.log_emit[state][first_symbol]      # log space: + not *
      self.update_matrix(self.state_index[state], 0, score, -1)

    # STEP 2: recursion. Three loops: column -> current state -> previous state
    for column in range(1, num_positions):
      symbol = observations[column]
      for current_state in self.states:
        best_candidate = -np.inf
        best_previous  = self.states[0]
        for previous_state in self.states:
          candidate = (self.score_matrix[self.state_index[previous_state], column - 1]
                       + self.log_trans[previous_state][current_state])
          if candidate > best_candidate:
            best_candidate = candidate
            best_previous  = previous_state
        score = best_candidate + self.log_emit[current_state][symbol]
        self.update_matrix(self.state_index[current_state], column, score,
                           self.state_index[best_previous])

    # STEP 3: termination. Best state in the LAST column only
    last_column    = num_positions - 1
    best_final_row = int(np.argmax(self.score_matrix[:, last_column]))
    best_log_prob  = self.score_matrix[best_final_row, last_column]

    # STEP 4: traceback
    path = self.traceback(best_final_row)
    return path, best_log_prob