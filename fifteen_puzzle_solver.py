import heapq

class PuzzleNode:
    def __init__(self, state, parent=None, move=None, g_cost=0, goal_state_map=None):
        self.state = state  # (tuple of tuples)
        self.parent = parent
        self.move = move # (dr, dc) or a description
        self.g_cost = g_cost # Cost from start
        self._goal_state_map = goal_state_map # Precomputed map of tile -> (r, c) for goal
        self.h_cost = self._calculate_manhattan_distance()
        self.f_cost = self.g_cost + self.h_cost
        self.empty_pos = self._find_empty_tile()

    def _find_empty_tile(self):
        for r in range(4):
            for c in range(4):
                if self.state[r][c] == 0: # 0 represents the empty tile
                    return (r, c)
        return None # Should not happen in a valid puzzle

    def _calculate_manhattan_distance(self):
        if self._goal_state_map is None:
            # Fallback if no map provided (should be provided by solver)
            # print("Warning: _goal_state_map not provided to PuzzleNode, using default standard goal.")
            temp_goal_map = {}
            # Standard goal: [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,0]]
            val = 1
            for r_idx in range(4):
                for c_idx in range(4):
                    if r_idx == 3 and c_idx == 3:
                        temp_goal_map[0] = (r_idx, c_idx)
                    else:
                        temp_goal_map[val] = (r_idx, c_idx)
                        val += 1
            current_map = temp_goal_map
        else:
            current_map = self._goal_state_map
        
        distance = 0
        for r in range(4):
            for c in range(4):
                tile_value = self.state[r][c]
                if tile_value != 0: # Don't count the empty tile
                    goal_r, goal_c = current_map[tile_value]
                    distance += abs(r - goal_r) + abs(c - goal_c)
        return distance

    def get_neighbors(self):
        neighbors = []
        r, c = self.empty_pos
        # Moves: (dr, dc) -> Right, Left, Down, Up
        possible_moves = [(0, 1), (0, -1), (1, 0), (-1, 0)] 

        for dr, dc in possible_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4: # Check bounds
                new_state_list = [list(row) for row in self.state]
                # Swap empty tile with the neighbor tile
                new_state_list[r][c], new_state_list[nr][nc] = new_state_list[nr][nc], new_state_list[r][c]
                new_state_tuple = tuple(tuple(row) for row in new_state_list)
                # Pass the goal_state_map to new nodes for consistent h_cost calculation
                neighbors.append(PuzzleNode(new_state_tuple, parent=self, move=(dr,dc), g_cost=self.g_cost + 1, goal_state_map=self._goal_state_map))
        return neighbors

    # For priority queue comparison (heapq is a min-heap)
    def __lt__(self, other):
        if self.f_cost == other.f_cost:
            return self.h_cost < other.h_cost # Tie-breaking: prefer smaller h_cost
        return self.f_cost < other.f_cost

    # For visited set (to store states in a set or as dict keys)
    def __hash__(self):
        return hash(self.state)

    def __eq__(self, other):
        return isinstance(other, PuzzleNode) and self.state == other.state

def get_inversions_count(flat_list_no_zero):
    count = 0
    n = len(flat_list_no_zero)
    for i in range(n):
        for j in range(i + 1, n):
            if flat_list_no_zero[i] > flat_list_no_zero[j]:
                count += 1
    return count

def get_empty_tile_row_from_bottom(state_tuple, N=4): # 1-indexed from bottom
    for r in range(N):
        for c in range(N):
            if state_tuple[r][c] == 0:
                return N - r # If r=0 (top row), N-0=N (Nth row from bottom). If r=N-1 (bottom row), N-(N-1)=1 (1st row from bottom)
    return -1 # Should not happen

def is_solvable_standard(initial_state_tuple, N=4):
    """
    Checks solvability for a standard N*N puzzle where the goal state has the empty tile 
    at the last position (bottom-right).
    N: grid dimension (e.g., 4 for 15-puzzle)
    """
    flat_list = [tile for row in initial_state_tuple for tile in row]
    # Inversion count does not include the empty tile (0)
    flat_list_no_zero = [tile for tile in flat_list if tile != 0]
    
    inversions = get_inversions_count(flat_list_no_zero)
    
    if N % 2 == 1: # Odd grid size (e.g., 3x3 8-puzzle)
        # Solvable if the number of inversions is even.
        return inversions % 2 == 0
    else: # Even grid size (e.g., 4x4 15-puzzle)
        # Solvable if:
        # (number of inversions) + (row of the empty space, counted from bottom, 1-indexed) is odd.
        # OR, more commonly stated:
        # If blank is on an even row counting from the bottom (e.g. 2nd or 4th), inversions must be odd.
        # If blank is on an odd row counting from the bottom (e.g. 1st or 3rd), inversions must be even.
        empty_row_from_bottom = get_empty_tile_row_from_bottom(initial_state_tuple, N)
        
        if empty_row_from_bottom % 2 == 1: # Blank on an odd row from bottom
            return inversions % 2 == 0 # Solvable if inversions are even
        else: # Blank on an even row from bottom
            return inversions % 2 != 0 # Solvable if inversions are odd

def solve_15_puzzle(initial_state_list, goal_state_list):
    initial_state_tuple = tuple(tuple(row) for row in initial_state_list)
    goal_state_tuple = tuple(tuple(row) for row in goal_state_list)

    # Precompute goal positions for heuristic, passed to PuzzleNode
    goal_positions_map = {}
    for r_idx, row_val in enumerate(goal_state_tuple):
        for c_idx, tile_val in enumerate(row_val):
            goal_positions_map[tile_val] = (r_idx, c_idx)

    start_node = PuzzleNode(initial_state_tuple, g_cost=0, goal_state_map=goal_positions_map)

    if start_node.state == goal_state_tuple:
        return [initial_state_tuple], 0, 0 # Path_states, nodes_expanded, num_moves

    # open_set_heap: a min-priority queue storing PuzzleNode objects
    open_set_heap = []
    heapq.heappush(open_set_heap, start_node)
    
    # open_set_g_costs: dictionary to keep track of the lowest g_cost found so far for states in the open_set_heap.
    # Key: state_tuple, Value: g_cost
    # This helps to avoid redundant processing if a state is added to heap multiple times with different paths.
    open_set_g_costs = {start_node.state: start_node.g_cost}
    
    # closed_set: stores states (tuples) that have been expanded (i.e., for which neighbors were generated).
    # With a consistent heuristic, once a node is popped from open_set_heap and processed,
    # we've found the optimal path to it.
    closed_set = set() 
    
    nodes_expanded_count = 0

    while open_set_heap:
        current_node = heapq.heappop(open_set_heap)

        # If this state is already in closed_set, it means we've processed the optimal path to it before.
        # This can happen if a state was added to the heap multiple times with different f_costs.
        if current_node.state in closed_set:
            continue 
        
        closed_set.add(current_node.state)
        # Once moved to closed, we can conceptually remove from open_set_g_costs, though not strictly necessary for logic.
        # if current_node.state in open_set_g_costs:
        #    del open_set_g_costs[current_node.state]


        nodes_expanded_count += 1

        if current_node.state == goal_state_tuple:
            path_states = []
            temp = current_node
            while temp: # Backtrack to reconstruct path
                path_states.append(temp.state)
                temp = temp.parent
            return path_states[::-1], nodes_expanded_count, len(path_states) - 1 # Path, expanded_nodes, num_moves

        for neighbor_node in current_node.get_neighbors():
            if neighbor_node.state in closed_set:
                continue # Already found optimal path to this neighbor

            # If this neighbor is not yet in open_set_g_costs or we found a shorter path to it
            if neighbor_node.g_cost < open_set_g_costs.get(neighbor_node.state, float('inf')):
                open_set_g_costs[neighbor_node.state] = neighbor_node.g_cost
                heapq.heappush(open_set_heap, neighbor_node)
            
    return None, nodes_expanded_count, -1 # No solution found

def print_board(state_tuple):
    if state_tuple is None:
        print("状态为 None")
        return
    for row in state_tuple:
        # Represent 0 as '.' for better readability, ensure two spaces for numbers
        print(" ".join(str(tile if tile != 0 else '.').rjust(2) for tile in row))
    print("-" * 11) # separator

def main():
    # Standard Goal State for 15-Puzzle
    goal_state_config = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 0] # 0 represents the empty space
    ]

    # --- Example Initial States ---
    # Solvability is checked against the standard goal_state_config
    initial_state_config_1_easy = [ # 1 move to goal
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 0],
        [13, 14, 15, 12]
    ]
    
    initial_state_config_2_medium = [ # A known solvable state
        [1,  2,  3,  4],
        [5,  6,  0,  8], # Empty at (1,2). Row from bottom: 4-1=3 (odd).
        [9, 10,  7, 12], # Inversions: (8:7), (9:7), (10:7), (12:11), (14:11) -> 5 (odd).
        [13, 14, 11, 15] # Solvable: N=4 (even), empty on odd row from bottom (3rd), inversions odd (5) => This should be solvable.
                         # Rule: blank on odd row => inversions even. My check above is inverted. Let's recheck rule.
                         # Corrected Rule: For N even, blank on odd row from bottom -> inversions must be even.
                         # My initial_state_config_2_medium: 5 inversions (odd), blank on 3rd row from bottom (odd) -> NOT solvable by standard rule.
                         # Let's pick a confirmed solvable one.
    ]

    # A verified solvable 15-puzzle initial state (e.g. from a lecture or trustworthy source)
    # This one is known to be solvable and requires a few moves.
    initial_state_verified_solvable = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9, 10,  0, 11], # Empty at (2,2). Row from bottom: 4-2=2 (even).
        [13, 14, 15, 12] # Inversions: (11: (none for its list)), (15:12) -> 1 inversion (odd).
                         # N=4 (even), empty on even row from bottom (2nd), inversions odd (1) -> Solvable. This works.
    ]
    
    initial_state_config_3_slightly_harder = [ # Another solvable state
        [5,  1,  2,  3],
        [0,  6,  7,  4], # Empty at (1,0). Row from bottom: 4-1=3 (odd).
        [9, 10, 11,  8], # Inversions for [5,1,2,3,6,7,4,9,10,11,8,13,14,15,12]:
                         # 5: (1,2,3,4) -> 4
                         # 1,2,3: -
                         # 6: (4) -> 1
                         # 7: (4) -> 1
                         # 4: -
                         # 9: (8) -> 1
                         # 10: (8) -> 1
                         # 11: (8) -> 1
                         # 8: -
                         # 13: (12) -> 1
                         # 14: (12) -> 1
                         # 15: (12) -> 1
                         # Total: 4+1+1+1+1+1+1+1+1 = 12 (even)
        [13,14, 15, 12] # N=4 (even), empty on odd row (3rd), inversions even (12) -> Solvable. This works.
    ]


    puzzles_to_test = {
        "教程案例1 (1 步)": initial_state_config_1_easy,
        "教程案例2 (经验证可解)": initial_state_verified_solvable,
        "教程案例3 (稍复杂可解)": initial_state_config_3_slightly_harder,
    }
    
    print("十五数码问题 A* 算法求解器")

    for name, initial_state_data in puzzles_to_test.items():
        print(f"--- 正在解决: {name} ---")
        print("初始状态:")
        print_board(tuple(tuple(r) for r in initial_state_data))
        print("目标状态:")
        print_board(tuple(tuple(r) for r in goal_state_config))

        # Check solvability against the standard goal
        is_s = is_solvable_standard(tuple(tuple(r) for r in initial_state_data))
        if not is_s:
            print("此初始状态对于标准目标是不可解的。跳过求解。")
            print("-" * 30 + "\n")
            continue
        else:
            print("状态可解。正在求解...")

        solution_path, expanded_nodes, num_of_moves = solve_15_puzzle(initial_state_data, goal_state_config)

        if solution_path:
            print(f"找到解决方案! 移动步数: {num_of_moves}")
            print(f"扩展节点数: {expanded_nodes}")
            print("\n详细步骤:")
            for i, state_tuple in enumerate(solution_path):
                print(f"步骤 {i}: ") # i is 0-indexed, so step 0 is initial state
                print_board(state_tuple)
            # Optionally print path details
            # print("初始状态:")
            # print_board(solution_path[0])
        else:
            print("未找到解决方案 (可能由于搜索限制或问题本身)。")
            print(f"扩展节点数 (在停止前): {expanded_nodes}")
        print("-" * 30 + "\n")

if __name__ == '__main__':
    main() 