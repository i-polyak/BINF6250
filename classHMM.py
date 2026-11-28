from typing import Dict, List, Tuple
import time
import numpy as np

class HMM:
    """Hidden Markov model built from initial, transition, and emission probabilities.

    Attributes:
        init_probs (Dict[str, float]): initial probabilities as given, {state: probability}
        trans_probs (Dict[str, Dict[str, float]]): transitions as given, {from_state: {to_state: probability}}
        emit_probs (Dict[str, Dict[str, float]]): emissions as given, {state: {symbol: probability}}
        states (List[str]): hidden states in a fixed order, i.e. ['I', 'G']
        state_index (Dict[str, int]): each state's row number, i.e. {'I': 0, 'G': 1}
        alphabet (Set[str]): observable symbols, i.e. {'A', 'C', 'G', 'T'}
        log_init (Dict[str, float]): init_probs with every probability as a log
        log_trans (Dict[str, Dict[str, float]]): trans_probs with every probability as a log
        log_emit (Dict[str, Dict[str, float]]): emit_probs with every probability as a log
        score_matrix (np.ndarray): best-path score for each state at each position
        traceback_matrix (np.ndarray): row number of the winning previous state for each box
    """

    def __init__(
        self,
        init_probs: Dict[str, float],
        trans_probs: Dict[str, Dict[str, float]],
        emit_probs: Dict[str, Dict[str, float]]
    ) -> None:
        """Stores the model, gets the states and alphabet, checks the inputs, and converts to logs.

        Args:
            init_probs (Dict[str, float]): chance of starting in each state
            trans_probs (Dict[str, Dict[str, float]]): chance of moving from each state to each state
            emit_probs (Dict[str, Dict[str, float]]): chance of each state emitting each symbol

        Raises:
            ValueError: if the dictionaries fail any check in validate()

        Examples:
            >>> hmm = HMM(init_probs, trans_probs, emit_probs)
            >>> hmm.states
            ['I', 'G']
            >>> hmm.state_index
            {'I': 0, 'G': 1}
        """
        #Step 1. Store the model
        self.init_probs = init_probs  #the initial probabilities exactly as the user gave them
        self.trans_probs = trans_probs  #the transition probabilities exactly as the user gave them
        self.emit_probs = emit_probs  #the emission probabilities exactly as the user gave them

        #Step 2. Get the states and the alphabet from the dictionaries
        self.states = list(self.init_probs.keys())  #the state names from init_probs, kept in that order, i.e. ['I', 'G']
        self.state_index = {state:row for row, state in enumerate(self.states)}
        first_state = self.states[0]  #the first state in the list, i.e. 'I'
        self.alphabet = set(self.emit_probs[first_state].keys())  #the symbols that state can emit, i.e. {'A', 'C', 'G', 'T'}

        #Step 3. Check the model
        self.validate()  #runs all the model checks on the original probabilities; stops with an error if anything is wrong

        #Step 4. Convert every probability to its log
        #Silences warning about probabilities equal to zero. Calculation is correct regardless.
        with np.errstate(divide='ignore'):
            self.log_init = {state:np.log(probability) for state, probability in self.init_probs.items()}  #go through each state and its probability

            self.log_trans = {from_state:{to_state:np.log(probability) for to_state, probability in row.items()} for from_state, row in self.trans_probs.items()}  #go through each state's row of transitions and go through each destination state in the row

            self.log_emit = {state:{symbol:np.log(probability) for symbol, probability in row.items()} for state, row in self.emit_probs.items()}  #go through each state's row of emissions and go through each symbol in the row

        self.score_matrix = None  #score_matrix will hold the best-path score for each state at each position, later in initialize_matrix() and viterbi_algorithm()
        self.traceback_matrix = None  #traceback_matrix will hold the row number of the winning previous state for each box, later in initialize_matrix() and viterbi_algorithm()


    def validate(self) -> None:
        """Checks that the model's dictionaries match each other and are real probabilities.

        Raises:
            ValueError: with a message naming the check that failed
        """
        state_set = set(self.states)  #the states as a set so they can be compared, i.e. {'I', 'G'}

        #Same states everywhere
        if set(self.trans_probs.keys()) != state_set:  #the states in trans_probs don't match the states in init_probs
            raise ValueError("transition states don't match the initial states")  #stops with an error
        for from_state, row in self.trans_probs.items():  #go through each state's row of transitions
            if set(row.keys()) != state_set:  #this row's destination states don't match
                raise ValueError(f"transition row {from_state} has the wrong states")  #stops with an error
        if set(self.emit_probs.keys()) != state_set:  #the states in emit_probs don't match the states in init_probs
            raise ValueError("emission states don't match the initial states")  #stops with an error

        #Same symbols in every emission row
        same_state = [state for state, row in self.emit_probs.items() if set(row.keys()) != self.alphabet] # Identifies states with different symbols
        if same_state: raise ValueError(f"emission row {same_state[0]} has different symbols")

        #No negative probabilities
        if any(probability < 0 for probability in self.init_probs.values()): raise ValueError("initial probabilities can't be negative")
        if any(probability < 0 for row in self.trans_probs.values() for probability in row.values()): raise ValueError("transition probabilities can't be negative")
        if any(probability < 0 for row in self.emit_probs.values() for probability in row.values()): raise ValueError("emission probabilities can't be negative")

        #Everything adds up to 1
        if not np.isclose(sum(self.init_probs.values()), 1):  #the initial probabilities don't add up to 1; isclose allows a tiny rounding difference
            raise ValueError("initial probabilities don't add up to 1")

        bad_trans_total = [s for s, row in self.trans_probs.items() if not np.isclose(sum(row.values()), 1)]
        if bad_trans_total: #the transition probabilities don't add up to 1; isclose allows a tiny rounding difference
            raise ValueError(f"transition row {bad_trans_total[0]} doesn't add up to 1")

        bad_emit_total = [s for s, row in self.emit_probs.items() if not np.isclose(sum(row.values()), 1)]
        if bad_emit_total: #the emission probabilities don't add up to 1; isclose allows a tiny rounding difference
            raise ValueError(f"emission row {bad_emit_total[0]} doesn't add up to 1")

    def check_observations(self, observations: str) -> None:
        """Checks that an observation sequence can be decoded by this model.

        Args:
            observations (str): observed symbols, i.e. "GGCACTGAA"

        Raises:
            ValueError: if observations is empty, or has a symbol not in the alphabet
        """
        if len(observations) == 0:  #the sequence is empty
            raise ValueError("observation sequence is empty")  #stops with an error

        unknown_symbols = set(observations) - self.alphabet  #the symbols in observations that are not in the alphabet, i.e. {'N'}
        if unknown_symbols:  #there is at least one unknown symbol
            raise ValueError(f"symbols not in the alphabet: {unknown_symbols}")  #stops with an error


    def initialize_score_matrix(self, num_states: int, num_positions: int) -> None:
        """Builds the empty score and traceback grids for one decode.

        Args:
            num_states (int): number of rows, one per hidden state
            num_positions (int): number of columns, one per observation

        Returns:
            None: sets score_matrix and traceback_matrix
        """
        self.score_matrix = np.full((num_states, num_positions), -np.inf)  #a grid with num_states rows and num_positions columns, every box set to negative infinity, meaning not filled in yet


    def initialize_traceback_matrix(self, num_states: int, num_positions: int) -> None:
        self.traceback_matrix = np.full((num_states, num_positions), -1, dtype=int)  #a grid the same size for whole numbers, every box set to -1, meaning "no previous state"


    def update_matrix(self, row: int, column: int, score: float, previous_row: int) -> None:
        """Writes one box: its score and the row of the previous state that won.

        Args:
            row (int): row number of the current state
            column (int): position in the observation sequence
            score (float): best-path score for this box
            previous_row (int): row number of the winning previous state (-1 in the first column)

        Returns:
            None: changes score_matrix and traceback_matrix
        """
        self.score_matrix[row, column] = score  #write the score in this box
        self.traceback_matrix[row, column] = previous_row  #write the row of the previous state that won in this box


    def traceback(self, best_final_row: int) -> List[str]:
        """Follows the pointers back from the best final state to build the path.

        Args:
            best_final_row (int): row number of the best state in the last column

        Returns:
            List[str]: hidden states from the first position to the last
        """
        path_rows = [best_final_row]  #a list that starts with the best final state's row
        last_column = self.traceback_matrix.shape[1] - 1  #shape[1] is the number of columns; minus 1 because index counting starts at 0

        for column in range(last_column, 0, -1):  #go from the last column back down to column 1; column 0 has no pointer
            path_rows.append(self.traceback_matrix[path_rows[-1], column])  #add the last row and the pointer to the end of path_rows

        path = [self.states[row] for row in reversed(path_rows)]  #turn the row number into its state name, i.e. 1 becomes 'G'

        return path


    def viterbi_algorithm(self, observations: str) -> Tuple[List[str], float]:
        """Finds the single most probable sequence of hidden states.

        Args:
            observations (str): observed symbols, i.e. "GGCACTGAA"

        Returns:
            Tuple[List[str], float]: the best path (one state per observation)
                and its log-probability

        Examples:
            >>> hmm.viterbi_algorithm("G")
            (['G'], -1.8326)
            >>> hmm.viterbi_algorithm("GG")
            (['G', 'G'], -3.5474)
            >>> hmm.viterbi_algorithm("GGCACTGAA")
            (['G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'], -13.9291)
        """
        #SETUP
        self.check_observations(observations)  #stops with an error if the sequence is empty or has an unknown symbol
        num_states = len(self.states)  #how many states there are, i.e. 2
        num_positions = len(observations)  #how many symbols are in observations, i.e. 9
        self.initialize_score_matrix(num_states, num_positions)  #builds the empty grids
        self.initialize_traceback_matrix(num_states, num_positions)

        #Step 7. First column (no max, no pointer)
        first_symbol = observations[0]  #the first symbol, i.e. 'G'
        scores = [self.log_init[state] + self.log_emit[state][first_symbol] for state in self.states] #log of starting in this state + log of this state emitting the first symbol
        for row, score in enumerate(scores):  #go through each state)
            self.update_matrix(row, 0, score, -1)  #write the score in this state's row, column 0, with -1 as the pointer

        #Step 8. Fill the rest of the columns, left to right
        for column in range(1, num_positions):  #go through column 1 to the last column
            symbol = observations[column]  #the symbol at this column
            for current_state in self.states:  #go through each state for this column
                candidates = [
                    self.score_matrix[self.state_index[previous_state], column - 1]
                    + self.log_trans[previous_state][current_state]
                    for previous_state in self.states
                ]
                best_previous_row = int(np.argmax(candidates))
                score = candidates[best_previous_row] + self.log_emit[current_state][symbol]  #best way in + log of current_state emitting this symbol
                self.update_matrix(self.state_index[current_state], column, score, best_previous_row)  #write the score, with the winning previous state's row as the pointer

        #Step 9. Finish
        last_column = num_positions - 1  #the number of the last column
        best_final_row = int(np.argmax(self.score_matrix[:, last_column]))  #the row with the biggest score in the last column; [:, last_column] means every row of that column
        best_log_prob = self.score_matrix[best_final_row, last_column]  #that biggest score

        #Step 10. Trace back
        path = self.traceback(best_final_row)  #follows the pointers back from the best final state

        return path, best_log_prob