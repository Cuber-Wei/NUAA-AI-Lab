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
        self.empty_tiles_pos = self._find_empty_tiles()

    def _find_empty_tiles(self):
        empty_tiles = []
        for r in range(4):
            for c in range(4):
                if self.state[r][c] == 0: # 0 represents an empty tile
                    empty_tiles.append((r, c))
        return empty_tiles

    def _calculate_manhattan_distance(self):
        if self._goal_state_map is None:
            return 0
            
        distance = 0
        for r in range(4):
            for c in range(4):
                tile_value = self.state[r][c]
                if tile_value != 0: # Don't count the empty tiles
                    if tile_value in self._goal_state_map: # Ensure the tile is in the goal map
                        goal_r, goal_c = self._goal_state_map[tile_value]
                        distance += abs(r - goal_r) + abs(c - goal_c)
        return distance

    def get_neighbors(self):
        neighbors = []
        # Moves: (dr, dc) -> Right, Left, Down, Up
        possible_moves_offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)] 

        for empty_idx, (r, c) in enumerate(self.empty_tiles_pos):
            # For each empty tile, try moving an adjacent numbered tile into it
            for dr_tile, dc_tile in possible_moves_offsets:
                nr_tile, nc_tile = r + dr_tile, c + dc_tile

                if 0 <= nr_tile < 4 and 0 <= nc_tile < 4: # Check bounds for the numbered tile
                    # Ensure we are not trying to swap an empty tile with another empty tile
                    # Although the logic is to move a numbered tile *into* an empty slot,
                    # nr_tile, nc_tile is the position of the tile *to be moved*.
                    # This tile must not be an empty one.
                    if self.state[nr_tile][nc_tile] == 0:
                        continue

                    new_state_list = [list(row) for row in self.state]
                    
                    # The numbered tile at (nr_tile, nc_tile) moves to the empty slot at (r,c)
                    new_state_list[r][c] = self.state[nr_tile][nc_tile]
                    # The original position of the numbered tile (nr_tile, nc_tile) becomes empty
                    new_state_list[nr_tile][nc_tile] = 0
                    
                    new_state_tuple = tuple(tuple(row) for row in new_state_list)
                    
                    # Create the new node
                    # The move description could be more sophisticated, e.g., (tile_value, (dr, dc))
                    neighbors.append(PuzzleNode(new_state_tuple, parent=self, move=(dr_tile, dc_tile), g_cost=self.g_cost + 1, goal_state_map=self._goal_state_map))
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

def solve_15_puzzle(initial_state_list, goal_state_list): # Renaming to solve_puzzle might be better
    initial_state_tuple = tuple(tuple(row) for row in initial_state_list)
    goal_state_tuple = tuple(tuple(row) for row in goal_state_list)

    goal_positions_map = {}
    for r_idx, row_val in enumerate(goal_state_tuple):
        for c_idx, tile_val in enumerate(row_val):
            if tile_val != 0: # Only map numbered tiles
                goal_positions_map[tile_val] = (r_idx, c_idx)

    start_node = PuzzleNode(initial_state_tuple, g_cost=0, goal_state_map=goal_positions_map)

    if start_node.state == goal_state_tuple:
        return [initial_state_tuple], 0, 0 # Path_states, nodes_expanded, num_moves

    open_set_heap = []
    heapq.heappush(open_set_heap, start_node)
    open_set_g_costs = {start_node.state: start_node.g_cost}
    closed_set = set() 
    nodes_expanded_count = 0

    while open_set_heap:
        current_node = heapq.heappop(open_set_heap)

        if current_node.state in closed_set:
            continue 
        
        closed_set.add(current_node.state)
        nodes_expanded_count += 1

        if current_node.state == goal_state_tuple:
            path_states = []
            temp = current_node
            while temp: 
                path_states.append(temp.state)
                temp = temp.parent
            return path_states[::-1], nodes_expanded_count, len(path_states) - 1

        for neighbor_node in current_node.get_neighbors():
            if neighbor_node.state in closed_set:
                continue

            if neighbor_node.g_cost < open_set_g_costs.get(neighbor_node.state, float('inf')):
                open_set_g_costs[neighbor_node.state] = neighbor_node.g_cost
                heapq.heappush(open_set_heap, neighbor_node)
            
    return None, nodes_expanded_count, -1

def read_puzzle_from_input():
    initial_state_list = []
    goal_state_list = []
    for _ in range(4):
        initial_state_list.append(list(map(int, input().split())))
    for _ in range(4):
        goal_state_list.append(list(map(int, input().split())))
    return initial_state_list, goal_state_list

def print_board(state_tuple):
    if state_tuple is None:
        print("状态为 None")
        return
    for row in state_tuple:
        print(" ".join(str(tile if tile != 0 else '.').rjust(3) for tile in row))
    print("-" * 15)

def main():
    initial_state_list, goal_state_list = read_puzzle_from_input()
    
    print("14数码问题 A* 算法求解器")
    print(f"--- 正在解决: 14数码问题 ---")
    print("初始状态:")
    print_board(tuple(tuple(r) for r in initial_state_list))
    print("目标状态:")
    print_board(tuple(tuple(r) for r in goal_state_list))

    solution_path, expanded_nodes, num_of_moves = solve_15_puzzle(initial_state_list, goal_state_list)

    if solution_path:
        print(f"找到解决方案! 移动步数: {num_of_moves}")
        print(f"扩展节点数: {expanded_nodes}")
        print("详细步骤:")
        for i, state_tuple in enumerate(solution_path):
            print(f"步骤 {i}:")
            print_board(state_tuple)
    else:
        print("未找到解决方案。")
        print(f"扩展节点数 (在停止前): {expanded_nodes}")
    print("-" * 30 + "")

if __name__ == '__main__':
    main() 