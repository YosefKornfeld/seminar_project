class HanoiSimulator:
    def __init__(self, n_disks):
        # STATE MANAGEMENT: Initial configuration
        # Peg 0: [n, ..., 1] (bottom to top)
        self.pegs = [list(range(n_disks, 0, -1)), [], []]
        self.n_disks = n_disks

    def execute_move(self, move):
        """
        Executes a move after 'four-layer validation'.
        move format: [disk_id, from_peg, to_peg]
        """
        disk_id, f, t = move

        # LAYER 1: Peg boundary conditions (0-2)
        if f not in [0, 1, 2] or t not in [0, 1, 2]:
            return False, f"Invalid peg indices: {f} to {t}"

        # LAYER 2: Verify source peg contains disks
        if not self.pegs[f]:
            return False, f"Source peg {f} is empty"

        # LAYER 3: Confirm specified disk is topmost
        if self.pegs[f][-1] != disk_id:
            return False, f"Disk {disk_id} is not at the top of peg {f}"

        # LAYER 4: Enforce size ordering constraint
        if self.pegs[t] and self.pegs[t][-1] < disk_id:
            return False, f"Illegal move: Disk {disk_id} is larger than {self.pegs[t][-1]}"

        # VALIDATION SUCCESSFUL: Update state [cite: 962]
        self.pegs[f].pop()
        self.pegs[t].append(disk_id)
        return True, "Valid Move"

    def validate_full_solution(self, move_list):
        """
        Processes move lists and verifies goal state.
        """
        for i, move in enumerate(move_list):
            success, message = self.execute_move(move)
            if not success:
                return False, f"Failure at move {i}: {message}"

        # FINAL VERIFICATION: Target state achievement
        # Peg 2 must have all disks in order.
        is_solved = (len(self.pegs[2]) == self.n_disks)
        return is_solved, "Solved" if is_solved else "Target state not reached"