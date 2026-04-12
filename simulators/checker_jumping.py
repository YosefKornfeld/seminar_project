class CheckerJumpingSimulator:
    def __init__(self, n_checkers):
        self.n = n_checkers
        # Initial state: ['R', 'R', '_', 'B', 'B'] for n=2
        # [cite: 967, 997-998]
        self.board = (['R'] * n_checkers) + ['_'] + (['B'] * n_checkers)

        # Goal state: ['B', 'B', '_', 'R', 'R']
        # [cite: 968, 999]
        self.goal = (['B'] * n_checkers) + ['_'] + (['R'] * n_checkers)

    def execute_move(self, move):
        """
        Multi-layer validation as per Section A.2.2 .
        """
        color, f, t = move

        # 1. Boundary check
        if not (0 <= f < len(self.board) and 0 <= t < len(self.board)):
            return False, "Position out of bounds"

        # 2. Source color check
        if self.board[f] != color:
            return False, f"Expected {color} at position {f}, found {self.board[f]}"

        # 3. Target empty check
        if self.board[t] != '_':
            return False, f"Target position {t} is not empty"

        # 4. Directional and Move Type check [cite: 1013]
        dist = t - f
        if color == 'R':
            if dist <= 0: return False, "Red checkers cannot move backward"
            if dist > 2: return False, "Move distance too far"
        else:  # color == 'B'
            if dist >= 0: return False, "Blue checkers cannot move backward"
            if dist < -2: return False, "Move distance too far"

        # 5. Jump validation (must jump over opposite color) [cite: 970, 1013]
        if abs(dist) == 2:
            mid_pos = (f + t) // 2
            mid_piece = self.board[mid_pos]
            opposite_color = 'B' if color == 'R' else 'R'
            if mid_piece != opposite_color:
                return False, f"Illegal jump: must jump over {opposite_color}"

        # VALIDATION SUCCESS: Execute move [cite: 1014]
        self.board[t] = color
        self.board[f] = '_'
        return True, "Success"

    def check_goal(self):
        # Final goal state verification [cite: 1015]
        return self.board == self.goal