def get_hanoi_prompt(num_disks):
    """
    Generates the exact System and User prompts for the Tower of Hanoi
    based on 'The Illusion of Thinking' paper's methodology.
    """
    system_prompt = (
        "You are an AI assistant tasked with solving the Tower of Hanoi puzzle. "
        "You must provide your step-by-step reasoning and then output the final sequence of moves. "
        "Rules:\n"
        "1. Only one disk can be moved at a time.\n"
        "2. Each move consists of taking the upper disk from one of the stacks and placing it on top of another stack.\n"
        "3. No disk may be placed on top of a smaller disk.\n\n"
        "Format your final answer exactly as a Python list of lists: moves = [[disk_id, from_peg, to_peg], ...]"
    )

    user_prompt = (
        f"Solve the Tower of Hanoi puzzle with {num_disks} disks. "
        "There are three pegs: 0, 1, and 2. "
        f"Initially, all {num_disks} disks are on peg 0, stacked in decreasing order of size "
        f"(disk {num_disks} at the bottom, disk 1 at the top). "
        "The goal is to move all disks to peg 2."
    )

    return system_prompt, user_prompt

def get_river_crossing_prompt(n_pairs, boat_capacity):
    """
    Generates the prompts for the River Crossing puzzle.
    The rule is based on the safety constraint: Actors (a) cannot be with rival Agents (A) unless their own Agent is present.
    """
    system_prompt = (
        "You are an AI assistant tasked with solving a river crossing puzzle. "
        "You must provide your step-by-step reasoning and then output the final sequence of moves. "
        "Rules:\n"
        f"1. A boat can hold up to {boat_capacity} passengers.\n"
        "2. The boat cannot move empty. At least one person must drive the boat.\n"
        "3. Safety Constraint: If any rival Agent (A) is present at a location (a bank or the boat), an Actor (a) MUST have their own corresponding Agent (A) present to be safe.\n"
        "4. Both banks and the boat must be safe at all times.\n\n"
        "Format your final answer exactly as a Python list of lists, where each inner list contains the passenger IDs to cross in that move: moves = [['A1', 'a1'], ['A1'], ...]"
    )
    
    actors = ", ".join([f"a{i}" for i in range(1, n_pairs + 1)])
    agents = ", ".join([f"A{i}" for i in range(1, n_pairs + 1)])
    user_prompt = (
        f"Solve the river crossing puzzle with {n_pairs} pairs of Agents and Actors. "
        f"The Agents are {agents} and the Actors are {actors} (e.g. A1 is paired with a1). "
        "Initially, everyone is on the left bank. "
        "The goal is to safely move everyone to the right bank."
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
    
    system_prompt = (
        "You are an AI assistant tasked with solving a Blocks World puzzle. "
        "You must provide your step-by-step reasoning and then output the final sequence of moves. "
        "Rules:\n"
        "1. Only the topmost block of a stack can be moved.\n"
        "2. A block can be moved to the top of another stack or to an empty stack.\n\n"
        "Format your final answer exactly as a Python list of lists: moves = [['block_id', from_stack_index, to_stack_index], ...]"
    )
    
    user_prompt = (
        "Solve the Blocks World puzzle. "
        f"The initial state of the stacks is: {initial_stacks}. "
        f"The goal state of the stacks is: {goal_stacks}. "
        "Find the shortest sequence of moves to reach the exact goal state. "
        "Stacks are 0-indexed."
    )
    
    return system_prompt, user_prompt


def get_checker_jumping_prompt(n_checkers):
    """
    Generates the prompts for the 1D Checker Jumping puzzle.
    """
    system_prompt = (
        "You are an AI assistant tasked with solving the 1D Checker Jumping puzzle. "
        "You must provide your step-by-step reasoning and then output the final sequence of moves. "
        "Rules:\n"
        "1. Red checkers ('R') can only move to the right. Blue checkers ('B') can only move to the left.\n"
        "2. A checker can slide to an adjacent empty space.\n"
        "3. A checker can jump over exactly one opposite colored checker into an empty space immediately beyond it.\n"
        "4. A checker cannot move backward.\n\n"
        "Format your final answer exactly as a Python list of lists: moves = [['color', from_pos, to_pos], ...]"
    )
    
    initial_state = (['R'] * n_checkers) + ['_'] + (['B'] * n_checkers)
    goal_state = (['B'] * n_checkers) + ['_'] + (['R'] * n_checkers)
    
    user_prompt = (
        f"Solve the Checker Jumping puzzle with {n_checkers} Red checkers and {n_checkers} Blue checkers. "
        f"Initially, the board is: {initial_state}. "
        f"The goal is to reach the state: {goal_state}. "
        "Board positions are 0-indexed."
    )
    
    return system_prompt, user_prompt