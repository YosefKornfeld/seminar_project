class BlocksWorldSimulator:
    def __init__(self, initial_stacks, goal_stacks):
        """
        initial_stacks: e.g., [['A', 'B'], ['C', 'D'], []]
        goal_stacks: e.g., [['D', 'B', 'C', 'A'], [], []]
        """
        # State Management [cite: 1096]
        self.stacks = [list(s) for s in initial_stacks]
        self.goal_stacks = [list(s) for s in goal_stacks]

    def execute_move(self, move):
        """
        Performs three-layer validation.
        move format: [block_id, from_stack, to_stack]
        """
        block_id, f, t = move

        # 1. Verify stack indices are within bounds
        if not (0 <= f < len(self.stacks) and 0 <= t < len(self.stacks)):
            return False, f"Stack index out of bounds: {f} or {t}"

        # 2. Confirm the source stack contains blocks
        if not self.stacks[f]:
            return False, f"Source stack {f} is empty"

        # 3. Ensure the specified block is at the top (Top-block-only rule)
        if self.stacks[f][-1] != block_id:
            return False, f"Block {block_id} is not at the top of stack {f}"

        # VALIDATION SUCCESS: Execute transfer [cite: 1098]
        block = self.stacks[f].pop()
        self.stacks[t].append(block)
        return True, "Success"

    def check_goal(self):
        # Verify target goal state achievement [cite: 1099]
        return self.stacks == self.goal_stacks

    def validate_full_solution(self, move_list):
        """
        Validates a sequence of Blocks World moves and verifies the final state.
        Each move is expected to be: [block_id, from_stack, to_stack]
        """
        for i, move in enumerate(move_list):
            if not isinstance(move, (list, tuple)) or len(move) != 3:
                return False, f"Failure at move {i}: Invalid move structure {move}"
            
            success, message = self.execute_move(move)
            if not success:
                return False, f"Failure at move {i}: {message}"

        is_solved = self.check_goal()
        return is_solved, "Solved" if is_solved else "Target state not reached"