# Introduction
This project implements the Viterbi algorithm for hidden Markov models. A hidden Markov model describes a sequence of observations that were produced by a sequence of hidden states we can't see directly. In our example the observations are DNA bases, and the hidden states are CpG island and genome background. Given a model and an observation sequence, the Viterbi algorithm finds the single most probable sequence of hidden states. This is the decoding problem described by Rabiner (1989) and in Chapter 3 of Durbin et al. (1998).

The model is defined by three dictionaries supplied by the user. These hold the initial probabilities, the transition probabilities, and the emission probabilities. We built an `HMM` class that stores the model and derives the states and the alphabet from these dictionaries, so nothing is hard-coded. The class also checks that the inputs are consistent and are valid probabilities, and it converts every probability to log space to prevent numerical underflow on long sequences. The Viterbi method fills a dynamic programming grid with one row per state and one column per position. For each box it keeps a pointer to the winning previous state, then traces back from the best final state to return the most probable path and its log-probability.

The class is designed to grow over the next projects. Helper methods for building the grid, writing to it, and tracing back are kept separate so they can be reused by the algorithms in Projects 09 and 10.

The notebook project08.ipynb contains the implementation and a test cell for each method. The tests include hand-checked answers, invalid inputs, an underflow test on an 1,800-symbol sequence, and a 3-state model with a non-DNA alphabet. The notebook ends with a demonstration on the example data from the project instructions.

# Pseudocode
```
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
    # Silence warning message for this step only. Warning points to probabilities = 0 which is acceptable and not an error.
    with np.errstates(divide='ignore'):
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
    observations = observations.upper()
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
```

# Results
We implemented a number of tests to check if the algorithm is working correctly:
Using the example data structures in Project08 instructions:
```
# Test cell for __init__ Results:
states: ['I', 'G'] expected: ['I', 'G']
state_index: {'I': 0, 'G': 1} expected: {'I': 0, 'G': 1}
alphabet: {'T', 'G', 'A', 'C'} expected: {'A', 'C', 'G', 'T'}
log_init I: -1.6094 expected: -1.6094
log_trans G to G: -0.1054 expected: -0.1054
log_emit I, C: -0.9163 expected: -0.9163

# Test cell for validate() results:
initial probabilities don't add up to 1
transition row I doesn't add up to 1
emission states don't match the initial states
emission row G has different symbols
initial probabilities can't be negative
emission row I doesn't add up to 1
emission probabilities can't be negative

# Test cell for check_observations() results:
GG passed
GGCACTGAA passed
GGNA error: symbols not in the alphabet: {'N'}
error: observation sequence is empty

# Test cell for initialize_matrix() and update_matrix() results:
[[-inf -inf -inf]
 [-inf -inf -inf]]
[[-1 -1 -1]
 [-1 -1 -1]]
-1.8326
-1

# Test cell for traceback() results:
['G', 'G']
['I', 'I']

# Test cell for viterbi_algorithm() results:
G ['G'] -1.8326
GG ['G', 'G'] -3.5474
GGCACTGAA ['G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'] -13.9291
-2762.3828671147444
1800

# Test cell for a model with 3 states and a non-DNA alphabet (nothing hard-coded for 2 states or for DNA) results:
['Z'] -1.8326

# if __name__ == __main__ cell results: This cell uses the example data to generate a path.
Observation:     GGCACTGAA
States:          GGGGGGGGG
Log Probability: -13.929108456051065

# Ecoli test cell results: Genome size is 4,699,745 base pairs
Log Probability: -6426002.235054593 and first 10 states of the path: ['N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N']. Elapsed time: 36.088131 seconds
```

# Successes
* Successfully implemented the Viterbi algorithm using log probabilities and traceback to identify the most probable hidden-state sequence.
* Designed a flexible HMM class with reusable methods that can be expanded upon for the future HMM algorithm projects.
* Validated the implementation using hand-calculated examples, invalid inputs, and longer sequences, including the E. coli genome test case.

# Struggles
* Deciding how to structure our algorithm without starter code or functions.
* Figuring out how to design the HMM class to work with different numbers of hidden states and observation symbols, rather than making it specific to DNA sequences.
* Making sure our code wasn't specific to DNA and could work with different numbers of hidden states and observation symbols.
* Accounting for edge cases

# Personal Reflection
### Group Leader: Ildiko Polyak
I felt intimidated by this project not having guardrails and functions to guide us, on top of learning a new algorithm.  Chapter 3 of Durbin et al. primer was very helpful for understanding the Viterbi algorithm. After our group meeting, where we sketched out the frame of the project, it helped me turn that frame into a solid pseudocode. It was an interesting new challenge to think about how to keep our project flexible and open for future use, while still making sure it is accurate and works properly for what we need now, a very new way for me to approach the projects. Since this week’s project had no guardrails, I am looking forward to seeing how everyone else approached the design. I'm sure there will be some very cool differences and I'm looking forward to learning more by reviewing them.

### Other Member: Selin Uenal
Our group has worked together before, so I was confident in our ability to work well toghether, and was looking forward to working together again. I thought this project was an interesting change from our previous assignments since we had so much more freedom in how we designed and structured the code. One of the biggest things we had to think about was how to design our HMM class to be flexible and reusable, with methods that we could build on for the algorithms in the next projects instead than having to start from scratch each time. We also spent a good chunk of time testing edge cases. This really helped me better understand why validation and testing are important beyond just getting the expected output. I'm excited to see how we will build on our HMM class in the next project!

## Other Member: Ahmed Salman
TODO

# Citations
Blattner, F. R., Plunkett, G., 3rd, Bloch, C. A., Perna, N. T., Burland, V., Riley, M., Collado-Vides, J., Glasner, J. D., Rode, C. K., Mayhew, G. F., Gregor, J., Davis, N. W., Kirkpatrick, H. A., Goeden, M. A., Rose, D. J., Mau, B., & Shao, Y. (1997). The complete genome sequence of Escherichia coli K-12. Science (New York, N.Y.), 277(5331), 1453–1462. https://doi.org/10.1126/science.277.5331.1453

This study is the original paper where the E.coli genome sequence I used was produced. The genome I am using does include future revisions as well. If you want to download the genome to test for yourself, here is the link: https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000005845.2/

# Generative AI Appendix
Ahmed Salman - Claude AI (Sonnet 5.5) to generate a set of probabilities for the E.coli test. Without somewhat realistic values for the test the results would have been messy and mostly meaningless. The probabilities I got from Claude produced reasonable results with large stretches of the "native" state with a few stretches of "alien" state.
