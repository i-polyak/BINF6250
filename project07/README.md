# Introduction
This project implements the Burrows-Wheeler Transform (BWT) and FM-index backward search for exact string matching, the approach used by short-read aligners such as Bowtie and BWA. After a $ end marker is added to the text, the BWT is built both by sorting all rotations and from a suffix array. A count table and an occurrence table are built from the BWT, and backward search uses them to apply the LF mapping, processing the pattern right to left and narrowing a block of rows (lower to upper) until the matching rows remain or the block is empty. Matching rows are converted to text positions through the suffix array. The BWT can also be compressed and restored with run-length encoding.

All required functionality was completed. All nine functions were implemented and tested on small hand-worked examples, and find_match() was tested on patterns that occur once, occur several times, overlap, and do not occur.

# Pseudocode
```
BWT Algorithm
Phase A: Build the BWT
Step 1: Add the end marker. banana becomes banana$. The $ has ASCII value 36, which is smaller than every letter (A = 65, a = 97). So the row starting with $ always sorts to the top, and it marks where the text ends
Step 2: Make every rotation. Take the first letter and move it to the end, 7 times (one per character)
Step 3: Sort the rotations alphabetically. Each rotation remembers where it started in the original text
Step 4: Read down the last column. This gives the BWT (shortcut:  suffix array method)

Phase B: Build the index
Step 5: Build the count table. For each letter, count how many letters (ignoring $) are alphabetically smaller
Step 6: Build the occurrence table. Walk along the BWT annb$aa one position at a time. At each position, record a running tally of how many of each letter you’ve seen so far, including the current position

Phase C: Backward search
Step 7: Start with all rows. Set lower = 0 and upper = (length of the text including $) - 1. Then process the pattern right to left
	Each step uses the same two formulas from the slides:
	new lower = count[letter] + occur[letter][lower − 1] + 1. If lower is 0, use 0 in place of the occur term
	new upper = count[letter] + occur[letter][upper]
	If at any step lower > upper, the range is empty. The pattern isn’t there, so return []
Step 8: Turn rows into positions. Look up the surviving rows in the suffix array
	
Phase D: Compress
Step 9: Run-length encode, written as letter then run length.
Step 10: Run-length decode. Do the reverse: read a letter, read its number, and write that letter that many times

Project 07 compared to algorithm
| Function | Matches your… | What it does |
|---|---|---|
| `BWT(string)` | Steps 1–4 | builds the BWT using rotations |
| `suffix_array(string)` | Step 3 | returns the starting positions of the sorted rotations |
| `BWT_from_suffix_array(text, suffix_positions)` | Step 4 shortcut | builds the BWT from the suffix array |
| `cal_count(string)` | Step 5 | builds the count table |
| `cal_occur(bwt_string)` | Step 6 | builds the occurrence table |
| `update_range(lower, upper, count, occur, a)` | Step 7, one letter | applies the two formulas once and returns the new lower and upper |
| `find_match(query, reference)` | Steps 7–8, the whole search | runs the full search and returns the positions |
| `run_length_encode(bwt_string)` | Step 9 | encodes the Step 4 result |
| `run_length_decode(encoded)` | Step 10 | decodes it back |

Project 07 Pseudocode
def BWT(string: str) -> str:
    IF string doesn't end with $:
        add $ to end of string

    make an empty list to hold the rotations
    FOR each position in the text:
        make the roation that starts at that position
        add it to the list

    sort the list of rotations alphabetically

    make an empty result
    FOR each rotation in the sorted list:
        add the last letter of the rotation to the result
    
    return result

Test cell for BWT()
FOR each test case (input, expected answer):
    run BWT on the input
    print the input, the result, and the expected answer

def suffix_array(string: str) -> list[int]:
IF string does not end with $:
        add $ to end of text

    make an empty list to hold (suffix, starting position) pairs
    FOR each position in the text:
        make the suffix that starts at that position
        add the pair (suffix, position) to the list

    sort the list of pairs alphabetically by suffix

    make an empty result list
    FOR each pair in the sorted list:
            add the starting position to the result
    
    return result

Test cell for suffix_array()
FOR each test case (input, expected answer):
    run suffix_array on input
    print the input, the result, and the expected answer

def BWT_from_suffix_array(
  text: str, 
  suffix_positions: list[int]
  ) -> str:

    IF text does not end with $:
        add $ to end of text

    make an empty result
    FOR each position p in suffix_positions:
        IF p is 0:
            add the last letter of text to the result
        ELSE:
            add the letter at position p - 1 of text to the result
    
    return result

Test cell for BWT_from_suffix_array()
FOR each test case (text, suffix positions, expected answer):
    run BWT_from_suffix_array on the text and suffix positions
    print the inputs, the result, and the expected answer

from collections import Counter

def cal_count(string: str) -> dict[str, int]:
    tally how many times each letter appears in text, skipping $

        set a running total to 0
        make an empty result table
        for each letter, in alphabetical order:
            store the running total as this letter's count
            add this letter's tally to the running total

        return result table

Test cal_count()
FOR each test case (input, expected answer):
    run cal_count on the input
    print the input, the result, and the expected answer

def cal_occur(bwt_string: str) -> dict[str, list[int]]:
    find every different letter in bwt_string, including $
        FOR each of those letters:
            set its counter to 0
            give it an empty list

        FOR each position in bwt_string:
            add 1 to the counter of the letter at this position
            FOR each letter:
                add its current counter to the end of its list
        
        return table of lists

Test cell for cal_occur
FOR each test case (input, expected answer):
    run_cal occur on the input
    print the input, the result, and the expected answer

def update_range(
  lower: int, 
  upper: int, 
  count: dict[str, int], 
  occur: dict[str, list[int]], 
  a: str) -> tuple[int, int]:

  IF lower is 0:
        letters above the block = 0
    ELSE:
        letters above the block = occur[the letter][lower - 1]

    new lower = count[the letter] + letters above the block + 1
    new upper = count[the letter] + occur[the letter][upper]

    return new lower, new upper

Test update_range()
count = cal_count of bananan
occur = cal_occur of annb$aa
FOR each test case (lower, upper, letter, expected answer):
    run update_range
    print the inputs, the result, and the expected answer

def find_match(query: str, reference: str) -> list[int]:
    IF query is empty:
        return an empty list
    
    Build Everything From The Reference
    IF reference does not end with $:
        add $ to end of reference
    suffix_positions = suffix_array(reference)
    bwt_string = BWT_from_suffix_array(reference, suffix_positions)
    count = cal_count(reference)
    occur = cal_occur(bwt_string)

    Search
    lower = 0
    upper = length of bwt_string - 1

    for each letter in query, from right to left:
        IF the letter is not in count:
            #return an empty list
        lower, upper = update_range(lower, upper, count, occur, the letter)
        IF lower > upper:
            return an empty list

    Turn Rows Into Positions
    make an empty result list
    FOR each row from lower to upper:
        add suffix_positions[row] to the result
    sort the result from smallest to largest

    return result

Test cell for find_match()
FOR each test case (query, reference, expected answer):
    run find_match
    print the inputs, the result, and the expected answer

def run_length_encode(bwt_string: str) -> str:
    IF bwt_string is empty:
        return an empty string
    
    make an empty result
    current letter =  the first letter of bwt_string
    run length = 1

    FOR each letter after the first one:
        IF it is the same as the current letter:
            add 1 to the run length
        ELSE:
            add the current letter and its run length to the result
            current letter = this letter
            run length = 1
        
    add the current letter and its run length to the result
    return result

Test cell for run_length_encode()
FOR each test case (input, expected answer):
    run run_length_encode on the input
    print the input, the result, and the expected answer

def run_length_decode(encoded: str) -> str:
    make an empty result
    start reading at position 0

    while there is still unread text:
        read one character: this is the letter
        move forward one position

        make an empty holder for the digits
        WHILE the current character is a digit:
            add it to the digit holder
            move forward one position

        turn the digit holder into a number
        add the letter to the result that many times

    return result

Test cell for run_length_decode()
FOR each test case (input, expected answer)
    run run_length_decode on the input
    print the input, the result, and expected answer
```

# Results
'BWT()'
lo$oogg
annb$aa

'suffix_array()'
[6, 3, 0, 5, 2, 4, 1]
[6, 5, 3, 1, 0, 4, 2]

'BWT_from_suffix_array()'
annb$aa
lo$oogg

'cal_count()'
ATGACG {'A': 0, 'C': 2, 'G': 3, 'T': 5} {'A': 0, 'C': 2, 'G': 3, 'T': 5} True
banana {'a': 0, 'b': 3, 'n': 4} {'a': 0, 'b': 3, 'n': 4} True

'cal_occur'
{'$': [0, 0, 1, 1, 1], 'A': [1, 1, 1, 1, 1], 'C': [0, 0, 0, 1, 1], 'G': [0, 1, 1, 1, 2]}
{'$': [0, 0, 0, 0, 1, 1, 1], 'a': [1, 1, 1, 1, 1, 2, 3], 'b': [0, 0, 0, 1, 1, 1, 1], 'n': [0, 1, 2, 2, 2, 2, 2]}

'update_range()'
0 6 a (1, 3) (1, 3) True
1 3 n (5, 6) (5, 6) True
5 6 a (2, 3) (2, 3) True
1 3 b (4, 4) (4, 4) True
5 6 n (7, 6) (7, 6) True

'find_match()'
banana banana [0] [0] True
a banana [1, 3, 5] [1, 3, 5] True
ana banana [1, 3] [1, 3] True
xyz banana [] [] True
nab banana [] [] True
go googol [0, 3] [0, 3] True

'run_length_encode()'
aaabbc a3b2c1 a3b2c1 True
annb$aa a1n2b1$1a2 a1n2b1$1a2 True
   True
Note: The third run_length_encode() line looks blank because it’s the empty-string test, so the input and result are both empty.

'run_length_decode()'
aaabbc a3b2c1 a3b2c1 True round trip: True
annb$aa a1n2b1$1a2 a1n2b1$1a2 True round trip: True
aaaaaaaaaaaa a12 a12 True round trip: True

# Successes
`find_match()` correctly handled all four types of patterns. The pattern banana occurs once in banana, the single letter a occurs several times, ana overlaps itself and was found at positions 1 and 3, and xyz and nab do not occur and returned empty lists.

The two methods of building the BWT, sorting all rotations and using the suffix array, produced the same transform for both banana and googol, confirming that the shortcut matches the original method.

Working the examples out by hand before testing showed that the `cal_occur()` docstring example for annb$aa is incorrect. Our code gives the correct occurrence table, which matches the hand-worked version.

Two edge cases that could fail without any error message were handled correctly. In `update_range()`, when lower is 0, the code uses 0 for the occurrence count instead of `occur[a][-1]`, which in Python would return the last value in the list rather than 0. In `run_length_decode()`, runs longer than nine characters are read as multi-digit numbers, so a12 correctly decodes to twelve a’s.

# Struggles
The `cal_occur()` docstring example for annb$aa contains an error. Since annb$aa begins with a, the a list should start at 1, giving [1, 1, 1, 1, 1, 2, 3], but the docstring starts it at 0. The n list has the same problem, and should be [0, 1, 2, 2, 2, 2, 2]. Because the code produces the correct values, its output does not match the docstring, which could be mistaken for a bug in the code. Working the occurrence table out by hand showed that the code was right and the docstring was wrong.

The note in `update_range()` says the function assumes `occur[a][-1] = 0`, which is misleading in Python. In Python, position -1 returns the last item in a list, not 0, so when lower is 0, `occur[a][lower - 1]` returns the final tally instead of 0. This produces a wrong search range without any error message. The code handles this by checking whether lower is 0 and using 0 for the occurrence count in that case.

The notebook’s pseudocode for `BWT()` says to return both the transformed string and the position of the original text in the sorted rotations, but the function’s docstring and examples return only the transformed string. The code follows the docstring, since its examples define the expected output.

The count table and the occurrence table were difficult to keep separate at first because they look similar. The count table holds one fixed number per character, the number of characters alphabetically smaller than it, excluding $. The occurrence table is a running tally that changes at every position of the BWT. Working out both tables by hand for banana made the difference clear.

Backward search was the hardest part of the algorithm to follow. The pattern is processed from right to left, and the block of rows does not just shrink but moves to a different part of the sorted table with each character. Working through the search one character at a time, with each number traced back to the table it came from, was needed before the formulas made sense.

# Reflection and Adaptive Learning
The assignment’s design questions ask how we would check that the inverse transform really inverts the forward transform, we thought about it as a group but did not implement it. The inverse relies on the LF mapping and the $ end marker, starting at the $ row (row 0), the last-column character in that row is the character that comes before it in the original text, and the LF mapping gives the row where that same character appears in the first column. Repeating this until $ is reached, then reversing the collected characters, rebuilds the text. To check it, we would run a round-trip test, confirming that inverse_BWT(BWT(text)) returns the original text, on the same test strings used for the other functions. The $ is required for this, without it, the starting row and stopping point are unknown, and a text like "abab" has repeated rotations that make the transform impossible to undo uniquely. The checks we did run follow the same round-trip idea. Both BWT methods produced the same transform for banana and googol, and run_length_decode(run_length_encode(text)) returned the original text in every test.

# Personal Reflections
## Ildiko Polyak
I was thoroughly confused after the lecture and dreading this assignmnet.  After reading more about the algorithm in my textbook and working through each portion by hand with a simple test case, the parts made sense.  By focusing on each function, I was able to write really basic pseudocode that I could scale up and transfer into more specific pseudocode for all the functions.  By focusing on each small part, I was able to piece together the algorithm as whole, otherwise, I would never have been able to tackle the project all at once.  Dianah and Abigail were helpful in writing the actual code for it, as this is still my greatest weakness in the class and I learn a lot by seeing how other people write different code for the same parts.

## Dianah Kasemir
The hardest part for me was understanding how the BWT could be reversed. It finally clicked when I tried rebuilding short words like "mama" and "cocoa" myself and could see the original word come back. I made a few mistakes along the way, like accidentally overwriting my input, forgetting to put quotes around $, and getting lists that were longer than expected because of repeated letters. These mistakes taught me to slow down and pay closer attention to what each line of code was doing. Working with Ildiko and Abigail made the project feel more manageable.

## Abigail Ackor
This project seemed daunting at first just because of the length of it. However, once we worked out our strategy as a group it went by faster than i anticipated. The code made sense and was a lot of iterations on itself which made identifying what different parts were doing easier. We had great pseudocode to start from Ildiko which made the formulation a lot easier.

# Generative AI Appendix
Antropic Claude Opus 5.5 was used to confirm results from hand written test cases for each function prior to writing pseudocode and code. This helped confirm that errors existed in the docstring and were not mistakes made from misunderstanding. 
