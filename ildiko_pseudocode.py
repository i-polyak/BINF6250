#from typing import Dict, Tuple  (type labels used in the method signatures)
#import numpy as np  (needed for np.full(), np.logaddexp.reduce(), np.exp(), np.isclose(), np.allclose())
#from hmm_model import HMM  (the Project 08 class, from hmm_model.py in the same folder)


class HMM09(HMM):
    """Hidden Markov model with the Forward, Backward, and Forward-Backward algorithms.

    Builds on the Project 08 HMM class in hmm_model.py, so it keeps __init__(),
    validate(), check_observations(), the log tables, and viterbi_algorithm().

    Attributes:
        tolerance (float): tolerance for the correctness checks in forward_backward()
    """

    #tolerance = 1e-9  (one tolerance used by every check; written here so Project 08's __init__() stays unchanged)


    def new_matrix(self, num_positions: int) -> np.ndarray:
        """Builds an empty grid for any algorithm: one row per state, one column per position.

        Args:
            num_positions (int): number of columns, one per observation

        Returns:
            np.ndarray: grid filled with -inf (log of 0), rows in the same order as self.states
        """
        #return np.full((len(self.states), num_positions), -np.inf)  (empty log grid; -inf means "not filled in yet")


    def forward(self, observations: str) -> Tuple[np.ndarray, float]:
        """Fills the forward table left to right and computes log P(x).

        Args:
            observations (str): observed symbols, i.e. "ATGCAA"

        Returns:
            Tuple[np.ndarray, float]: the forward table (log values) and log P(x)
        """
        #self.check_observations(observations)  (from Project 08; stops with an error if the sequence is empty or has an unknown symbol)
        #num_positions = len(observations)  (how many columns)
        #forward_matrix = self.new_matrix(num_positions)  (empty grid for the forward values)

        #first_symbol = observations[0]  (the first letter)
        #FOR state in self.states:  (first column, the same as Viterbi)
            #forward_matrix[self.state_index[state], 0] = self.log_init[state] + self.log_emit[state][first_symbol]  (log of start x emit)

        #FOR column in range(1, num_positions):  (left to right)
            #symbol = observations[column]  (this column's letter)
            #FOR current_state in self.states:
                #incoming = []  (empty list; will hold every way into this box)
                #FOR previous_state in self.states:
                    #incoming.append(forward_matrix[self.state_index[previous_state], column - 1] + self.log_trans[previous_state][current_state])  (one way in: box to the left + log of moving here)
                #forward_matrix[self.state_index[current_state], column] = np.logaddexp.reduce(incoming) + self.log_emit[current_state][symbol]  (ADD all ways in, then add log emission; Viterbi used max here)

        #log_prob = np.logaddexp.reduce(forward_matrix[:, -1])  (add up the last column = log P(x))
        #return forward_matrix, log_prob


    def backward(self, observations: str) -> Tuple[np.ndarray, float]:
        """Fills the backward table right to left and computes log P(x).

        Args:
            observations (str): observed symbols, i.e. "ATGCAA"

        Returns:
            Tuple[np.ndarray, float]: the backward table (log values) and log P(x)
        """
        #self.check_observations(observations)  (from Project 08; stops with an error if the sequence is empty or has an unknown symbol)
        #num_positions = len(observations)  (how many columns)
        #backward_matrix = self.new_matrix(num_positions)  (empty grid for the backward values)
        #backward_matrix[:, -1] = 0  (last column = log of 1; nothing left to explain)

        #FOR column in range(num_positions - 2, -1, -1):  (right to left, from the second-to-last column down to column 0)
            #next_symbol = observations[column + 1]  (the emission comes from the NEXT position)
            #FOR current_state in self.states:
                #outgoing = []  (empty list; will hold every way out of this box)
                #FOR next_state in self.states:
                    #outgoing.append(self.log_trans[current_state][next_state] + self.log_emit[next_state][next_symbol] + backward_matrix[self.state_index[next_state], column + 1])  (one way out: move + next emission + backward value to the right)
                #backward_matrix[self.state_index[current_state], column] = np.logaddexp.reduce(outgoing)  (ADD all ways out)

        #first_symbol = observations[0]  (the first letter)
        #finish_terms = []  (empty list; one term per state)
        #FOR state in self.states:
            #finish_terms.append(self.log_init[state] + self.log_emit[state][first_symbol] + backward_matrix[self.state_index[state], 0])  (start x first emission x backward value; the first emission only appears here)
        #log_prob = np.logaddexp.reduce(finish_terms)  (log P(x); must match forward)
        #return backward_matrix, log_prob


    def forward_backward(self, observations: str) -> Dict[str, object]:
        """Combines the forward and backward tables into posterior probabilities.

        Args:
            observations (str): observed symbols, i.e. "ATGCAA"

        Returns:
            Dict[str, object]: "posterior" (regular probabilities; each column sums to 1),
                "forward" and "backward" (log tables), and "log_prob" (log P(x))

        Raises:
            ValueError: if forward and backward disagree, or a posterior column doesn't sum to 1
        """
        #forward_matrix, forward_log_prob = self.forward(observations)  (run forward, keep its table)
        #backward_matrix, backward_log_prob = self.backward(observations)  (run backward, keep its table)

        #IF not np.isclose(forward_log_prob, backward_log_prob, rtol=self.tolerance, atol=0):  (check 1: both directions must agree)
            #raise ValueError("forward and backward log P(x) don't match")

        #posterior_matrix = np.exp(forward_matrix + backward_matrix - forward_log_prob)  (multiply the tables and divide by P(x); in logs that's add and subtract; exp turns them back into regular probabilities)

        #IF not np.allclose(posterior_matrix.sum(axis=0), 1, atol=self.tolerance):  (check 2: every column must sum to 1; axis=0 sums down each column)
            #raise ValueError("a posterior column doesn't sum to 1")

        #return {"posterior": posterior_matrix, "forward": forward_matrix, "backward": backward_matrix, "log_prob": forward_log_prob}  (everything Baum-Welch will need, so nothing gets recomputed)