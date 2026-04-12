class RiverCrossingSimulator:
    def __init__(self, n_pairs, boat_capacity):
        self.n_pairs = n_pairs
        self.k = boat_capacity
        self.boat_side = 0  # 0: Left, 1: Right

        # Initial State: All individuals on the left bank [cite: 1020, 1044]
        self.left_bank = set()
        for i in range(1, n_pairs + 1):
            self.left_bank.add(f"a{i}")  # Actor
            self.left_bank.add(f"A{i}")  # Agent
        self.right_bank = set()

    def is_state_safe(self, people_at_location):
        """
        The critical Safety Constraint [cite: 1024-1025, 1048].
        If any rival agent is present, the actor's own agent MUST be present.
        """
        actors = {p for p in people_at_location if p.startswith('a')}
        agents = {p for p in people_at_location if p.startswith('A')}

        for actor in actors:
            actor_id = actor[1:]
            own_agent = f"A{actor_id}"

            # Find if any rival agents are present
            rival_agents = agents - {own_agent}
            if rival_agents and own_agent not in agents:
                return False, f"Safety violation: Actor {actor} is with rival agents without their own agent."

        return True, ""

    def execute_move(self, move_passengers):
        """
        Processes a single boat move with multi-step validation [cite: 1048-1049].
        """
        # 1. Capacity Check
        if not (1 <= len(move_passengers) <= self.k):
            return False, f"Boat capacity violation: {len(move_passengers)} passengers."

        # 2. Presence Check: Are these people on the correct side?
        current_bank = self.left_bank if self.boat_side == 0 else self.right_bank
        if not all(p in current_bank for p in move_passengers):
            return False, "Move contains people not currently on the boat's side."

        # 3. Perform the move
        target_bank = self.right_bank if self.boat_side == 0 else self.left_bank
        for p in move_passengers:
            current_bank.remove(p)
            target_bank.add(p)

        # 4. Global Safety Check (Banks + Boat) [cite: 1025, 1048-1049]
        # Note: The 'move_passengers' are the people currently in the boat.
        for location, name in [(self.left_bank, "Left Bank"),
                               (self.right_bank, "Right Bank"),
                               (move_passengers, "Boat")]:
            safe, msg = self.is_state_safe(location)
            if not safe:
                return False, f"{name} {msg}"

        # Success: Switch boat side
        self.boat_side = 1 - self.boat_side
        return True, "Valid move"

    def check_goal(self):
        # Goal: Everyone on the right bank [cite: 1021, 1050]
        return len(self.right_bank) == (2 * self.n_pairs)