def get_hanoi_prompt(num_disks):
    """
    Generates the exact System and User prompts for the Tower of Hanoi
    based on 'The Illusion of Thinking' paper's methodology.
    """
    system_prompt = (
"""You are a helpful assistant. Solve this puzzle for me.
There are three pegs and n disks of different sizes stacked on the first peg. The disks are numbered from 1
(smallest) to n (largest). Disk moves in this puzzle should follow:
1. Only one disk can be moved at a time.
2. Each move consists of taking the upper disk from one stack and placing it on top of another stack.
3. A larger disk may not be placed on top of a smaller disk.
The goal is to move the entire stack to the third peg.
Example: With 3 disks numbered 1 (smallest), 2, and 3 (largest), the initial state is [[3, 2, 1], [], []], and a
solution might be:
moves = [[1 , 0 , 2] , [2 , 0 , 1] , [1 , 2 , 1] , [3 , 0 , 2] ,
[1 , 1 , 0] , [2 , 1 , 2] , [1 , 0 , 2]]
This means: Move disk 1 from peg 0 to peg 2, then move disk 2 from peg 0 to peg 1, and so on.
Requirements:
list of moves.
• When exploring potential solutions in your thinking process, always include the corresponding complete
• The positions are 0-indexed (the leftmost peg is 0).
• Ensure your final answer includes the complete list of moves in the format:
moves = [[disk id, from peg, to peg], ...]"""
    )

    user_prompt = (
f"""
I have a puzzle with {num_disks} disks of different sizes with
Initial configuration:
• Peg 0: {num_disks} (bottom),. . . 2, 1 (top)
• Peg 1: (empty)
• Peg 2: (empty)
Goal configuration:
• Peg 0: (empty)
• Peg 1: (empty)
• Peg 2: {num_disks} (bottom),. . . 2, 1 (top)
Rules:
• Only one disk can be moved at a time.
• Only the top disk from any stack can be moved.
• A larger disk may not be placed on top of a smaller disk.
Find the sequence of moves to transform the initial configuration into the goal configuration.
"""
    )

    return system_prompt, user_prompt

def get_river_crossing_prompt(n_pairs, boat_capacity):
    """
    Generates the prompts for the River Crossing puzzle.
    The rule is based on the safety constraint: Actors (a) cannot be with rival Agents (A) unless their own Agent is present.
    """
    system_prompt = (
        """You are a helpful assistant. Solve this puzzle for me.
You can represent actors with a1, a2, ... and agents with A1, A2, ... . Your solution must be a list of boat moves
where each move indicates the people on the boat. For example, if there were two actors and two agents, you
should return:
moves =[[" A2 " , " a2 "] , [" A2 "] , [" A1 " , " A2 "] , [" A1 "] , [" A1 " , " a1 "]]
which indicates that in the first move, A2 and a2 row from left to right, and in the second move, A2 rows from
right to left and so on.
Requirements:
• When exploring potential solutions in your thinking process, always include the corresponding complete
list of boat moves.
• The list shouldn't have comments.
• Ensure your final answer also includes the complete list of moves for final solution."""
    )
    
    user_prompt = (
f"""{n_pairs} actors and their {n_pairs} agents want to cross a river in a boat that is capable of holding only {boat_capacity} people at a
time, with the constraint that no actor can be in the presence of another agent, including while
riding the boat, unless their own agent is also present, because each agent is worried their rivals will
poach their client. Initially, all actors and agents are on the left side of the river with the boat. How should
they cross the river?"""
    )
    
    return system_prompt, user_prompt


import string

def generate_blocks_world_states(n):
    # Create list of letters based on required N
    all_blocks = list(string.ascii_uppercase[:n])
    mid = n // 2
    
    stack0 = all_blocks[:mid]
    stack1 = all_blocks[mid:]
    initial_state = [stack0, stack1, []]
    
    # Create goal state by interleaving the reversed lists
    goal_stack = []
    for b1, b0 in zip(reversed(stack1), reversed(stack0)):
        goal_stack.append(b1)
        goal_stack.append(b0)
        
    goal_state = [goal_stack, [], []]
    return initial_state, goal_state


def get_blocks_world_prompt(n):
    """
    Generates the prompts for the Blocks World puzzle for a given N (number of blocks).
    """
    initial_stacks, goal_stacks = generate_blocks_world_states(n)
    m = len(initial_stacks) - 1

    system_prompt = (
"""You are a helpful assistant. Solve this puzzle for me.
In this puzzle, there are stacks of blocks, and the goal is to rearrange them into a target configuration using a
sequence of moves where:
• Only the topmost block from any stack can be moved.
• A block can be placed either on an empty position or on top of another block.
Example: With initial state [["A", "B"], ["C"], []] and goal state [["A"], ["B"], ["C"]], a solution
might be:
moves = [[" C " , 1 , 2] , [" B " , 0 , 1]]
This means: Move block C from stack 1 to stack 2, then move block B from stack 0 to stack 1.
Requirements:
list of moves.
• When exploring potential solutions in your thinking process, always include the corresponding complete
• The positions are 0-indexed (the leftmost position is 0).
• Ensure your final answer also includes the complete list of moves for final solution in the format: moves =
[[block, from stack, to stack], ...]"""
    )

    user_prompt = (
f"""I have a puzzle with {n} blocks.
Initial state:
Stack 0: {initial_stacks[0]} (top)
Stack 1: {initial_stacks[1]} (top)
...
Stack {m}: {initial_stacks[m]} (top)
Goal state:
Stack 0: {goal_stacks[0]} (top)
Stack 1: {goal_stacks[1]} (top)
...
Stack {m}: {goal_stacks[m]} (top)
Find the sequence of moves to transform the initial state into the goal state. Remember that only the topmost
block of each stack can be moved."""
    )

    return system_prompt, user_prompt, initial_stacks, goal_stacks



def get_checker_jumping_prompt(n_checkers):
    """
    Generates the prompts for the 1D Checker Jumping puzzle.
    """
    system_prompt = (
"""You are a helpful assistant. Solve this puzzle for me.
On a one-dimensional board, there are red checkers (`R`), blue checkers (`B`), and one empty space (`_`). A
checker can move by either:
1. Sliding forward into an adjacent empty space, or
2. Jumping over exactly one checker of the opposite color to land in an empty space.
The goal is to swap the positions of all red and blue checkers, effectively mirroring the initial state.
Example: If the initial state is [`R`, `_`, `B`], the goal is to reach [`B`, `_`, `R`]. Your solution should be a list
of moves where each move is represented as [checker_color, position_from, position_to]. For example:
moves = [[`R`, 0, 1] , [`B`, 2, 0] , [`R`, 1, 2]]
This means: Move the red checker from position 0 to 1, then move the blue checker from position 2 to 0, and so
on.
Requirements:
list of moves.
• When exploring potential solutions in your thinking process, always include the corresponding complete
• The positions are 0-indexed (the leftmost position is 0).
• Ensure your final answer includes the complete list of moves for final solution in the format: moves =
[[checker_color, position_from, position_to], ...]"""
    )
    
    initial_state = (['R'] * n_checkers) + ['_'] + (['B'] * n_checkers)
    goal_state = (['B'] * n_checkers) + ['_'] + (['R'] * n_checkers)
    
    user_prompt = (
f"""I have a puzzle with {2*n_checkers+1} positions, where {n_checkers} red checkers (`R`) on left, {n_checkers} blue checkers (’B’) on right,
and one empty space (`_`) in between are arranged in a line.
Initial board: R R ... R _ B B ... B
Goal board: B B ... B _ R R ... R
Rules:
• A checker can slide into an adjacent empty space.
• A checker can jump over exactly one checker of the opposite color to land in an empty space.
• Checkers cannot move backwards (towards their starting side).
Find the sequence of moves to transform the initial board into the goal board."""
    )
    
    return system_prompt, user_prompt