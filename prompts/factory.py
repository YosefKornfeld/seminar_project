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

# Future expansion for the other puzzles:
# def get_river_crossing_prompt(num_actors): ...
# def get_blocks_world_prompt(num_blocks): ...