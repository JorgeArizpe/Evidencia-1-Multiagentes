from owlready2 import *
import agentpy as ap
import random

ontology = get_ontology("ontology.owl").load()

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.owl_instance = ontology.Position()
        self.owl_instance.x.append(x)
        self.owl_instance.y.append(y)
    def __repr__(self):
        return f"({self.x}, {self.y})"  
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y  
    def __hash__(self):
        return hash((self.x, self.y))  

class Robot(ap.Agent):
    def setup(self):
        while True:
            self.position = Position(random.randint(0, self.model.rows - 1), random.randint(0, self.model.cols - 1))
            if self.position not in self.model.occupied_positions:
                break
        self.model.occupied_positions.add(self.position)
        self.facing_direction = random.choice(["N", "S", "E", "O"])
        self.is_carrying_object = False
        self.target_object = None
        self.target_stack = None
        self.is_active = True
        self.steps = 0
        self.model.log.append(f"Robot {self.id} initialized at {self.position} facing {self.facing_direction}")

    def rotate_to(self, direction):
        if self.facing_direction != direction:
            self.facing_direction = direction
            self.model.log.append(f"Robot {self.id} rotated to face {direction}")

    def move_to(self, target):
        dx = target.x - self.position.x
        dy = target.y - self.position.y
        if abs(dx) > 0:
            direction = "S" if dx > 0 else "N"
            if self.facing_direction != direction:
                self.rotate_to(direction)
            else:
                self.position.x += 1 if dx > 0 else -1
                self.steps += 1
                self.model.log.append(f"Robot {self.id} moved to {self.position}")
        elif abs(dy) > 0:
            direction = "E" if dy > 0 else "O"
            if self.facing_direction != direction:
                self.rotate_to(direction)
            else:
                self.position.y += 1 if dy > 0 else -1
                self.steps += 1
                self.model.log.append(f"Robot {self.id} moved to {self.position}")

    def get_front_position(self):
        if self.facing_direction == "N":
            return Position(self.position.x - 1, self.position.y)
        elif self.facing_direction == "S":
            return Position(self.position.x + 1, self.position.y)
        elif self.facing_direction == "E":
            return Position(self.position.x, self.position.y + 1)
        elif self.facing_direction == "O":
            return Position(self.position.x, self.position.y - 1)

    def pick_object(self):
        target_position = self.get_front_position()
        if target_position in self.model.objects and not self.model.is_position_occupied(target_position):
            self.is_carrying_object = True
            self.model.remove_object(target_position)
            self.model.mark_position_occupied(self.position)
            self.model.unreserve_object(target_position)
            self.target_object = None
            self.model.log.append(f"Robot {self.id} picked up an object from {target_position}")

    def stack_object(self):
        target_position = self.get_front_position()
        if (
            target_position == self.model.active_stack
            and self.is_carrying_object
            and not self.model.is_stack_locked()
        ):
            self.model.lock_stack()
            self.is_carrying_object = False
            self.model.stack_object(target_position)
            self.model.mark_position_free(self.position)
            self.model.log.append(f"Robot {self.id} stacked an object at {target_position}")
            if self.model.stacks[target_position] >= 5:
                self.model.update_stack_position()
            self.model.unlock_stack()

    def plan(self):
        if not self.is_active:
            return
        if not self.is_carrying_object:
            if not self.target_object or self.model.is_position_occupied(self.target_object):
                self.target_object = self.model.get_closest_object_position(self.position)
                if self.target_object and not self.model.is_object_reserved(self.target_object):
                    self.model.reserve_object(self.target_object)
                    self.model.log.append(f"Robot {self.id} selected object at {self.target_object} as target")
            if self.target_object:
                if self.get_front_position() == self.target_object:
                    self.model.log.append(f"Robot {self.id} is in front of the target object at {self.target_object}")
                    self.pick_object()
                else:
                    self.move_to(self.target_object)
            else:
                self.is_active = False
                self.model.log.append(f"Robot {self.id} has no available target and is now inactive.")
        else:
            if not self.target_stack or self.target_stack != self.model.active_stack:
                self.target_stack = self.model.active_stack
                self.model.log.append(f"Robot {self.id} redirected to current active stack at {self.target_stack}")
            if (
                self.get_front_position() == self.target_stack
                and not self.model.is_stack_locked()
            ):
                self.model.log.append(f"Robot {self.id} is in front of the stack at {self.target_stack}")
                self.stack_object()
            else:
                self.move_to(self.target_stack)

class WarehouseSimulation(ap.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.occupied_positions = set()
        self.reserved_objects = set()
        self.active_stack_lock = False

    def is_stack_locked(self):
        return self.active_stack_lock
    def lock_stack(self):
        self.active_stack_lock = True
    def unlock_stack(self):
        self.active_stack_lock = False

    def is_position_occupied(self, position):
        return position in self.occupied_positions
    def mark_position_occupied(self, position):
        self.occupied_positions.add(position)
    def mark_position_free(self, position):
        self.occupied_positions.discard(position)

    def is_object_reserved(self, position):
        return position in self.reserved_objects
    def reserve_object(self, position):
        self.reserved_objects.add(position)
    def unreserve_object(self, position):
        self.reserved_objects.discard(position)

    def setup(self):
        self.rows = 10
        self.cols = 10
        self.central_position = Position(self.rows // 2, self.cols // 2)
        self.active_stack = self.central_position
        self.stacks = {self.active_stack: 0}
        self.log = []
        used_positions = set()
        self.objects = []
        while len(self.objects) < 20:
            obj_pos = Position(random.randint(0, self.rows - 1), random.randint(0, self.cols - 1))
            if obj_pos not in used_positions:
                self.objects.append(obj_pos)
                used_positions.add(obj_pos)
                self.log.append(f"Object initialized at {obj_pos}")
        self.robots = ap.AgentList(self, 5, Robot)
        self.register_in_ontology()

    def remove_object(self, position):
        if position in self.objects:
            self.objects.remove(position)

    def stack_object(self, position):
        if position not in self.stacks:
            self.stacks[position] = 0
        self.stacks[position] += 1
        if self.stacks[position] >= 5:
            self.update_stack_position()

    def update_stack_position(self):
        surrounding_offsets = [
            (-1, 0), (-1, 1), (0, 1), (1, 1),
            (1, 0), (1, -1), (0, -1), (-1, -1)
        ]
        for dx, dy in surrounding_offsets:
            new_stack = Position(self.central_position.x + dx, self.central_position.y + dy)
            if new_stack not in self.stacks or self.stacks[new_stack] < 5:
                self.active_stack = new_stack
                self.stacks[new_stack] = 0
                self.log.append(f"New active stack set at {self.active_stack}")
                for robot in self.robots:
                    if robot.is_carrying_object:
                        robot.target_stack = self.active_stack
                        self.log.append(f"Robot {robot.id} redirected to new stack at {self.active_stack}")
                return

    def get_closest_object_position(self, position):
        if not self.objects:
            return None
        return min(
            (obj for obj in self.objects if not self.is_object_reserved(obj)),
            key=lambda obj: abs(obj.x - position.x) + abs(obj.y - position.y),
            default=None
        )

    def detect_conflicts(self):
        planned_moves = {}
        for robot in self.robots:
            if robot.is_active:
                next_position = robot.get_front_position()
                if next_position in planned_moves:
                    self.log.append(
                        f"Conflict detected: Robot {robot.id} and Robot {planned_moves[next_position]} are moving to the same position {next_position}"
                    )
                else:
                    planned_moves[next_position] = robot.id

    def detect_and_resolve_conflicts(self):
        planned_moves = {}
        robots_to_wait = {}
        for robot in self.robots:
            if robot.is_active:
                next_position = robot.get_front_position()
                if next_position in planned_moves:
                    other_robot_id = planned_moves[next_position]
                    self.log.append(
                        f"Conflict detected: Robot {robot.id} and Robot {other_robot_id} are moving to the same position {next_position}"
                    )
                    if random.choice([True, False]):
                        robots_to_wait[robot.id] = 2
                        self.log.append(f"Robot {robot.id} will wait for 2 steps")
                    else:
                        robots_to_wait[other_robot_id] = 2
                        self.log.append(f"Robot {other_robot_id} will wait for 2 steps")
                else:
                    planned_moves[next_position] = robot.id
        for robot in self.robots:
            if robot.id in robots_to_wait:
                robot.is_active = False
                robot.wait_steps = robots_to_wait[robot.id]

    def step(self):
        self.detect_and_resolve_conflicts()
        for robot in self.robots:
            if hasattr(robot, "wait_steps") and robot.wait_steps > 0:
                robot.wait_steps -= 1
                if robot.wait_steps == 0:
                    robot.is_active = True
                    self.log.append(f"Robot {robot.id} is active again after waiting")
        if len(self.objects) == 0 and all(not robot.is_carrying_object for robot in self.robots):
            self.log.append("All tasks completed. Stopping simulation.")
            self.stop()
        self.robots.plan()

    def update(self):
        self.report('remaining_objects', len(self.objects))
        self.report('stacks', {pos: count for pos, count in self.stacks.items() if count > 0})
        self.report('robot_steps', {robot.id: robot.steps for robot in self.robots})
        if hasattr(self, 'log'):
            self.report('log', self.log)

    def register_in_ontology(self):
        self.owl_instance = ontology.WarehouseSimulation()
        self.owl_instance.rows.append(self.rows)
        self.owl_instance.cols.append(self.cols)
        for obj_pos in self.objects:
            pos_instance = ontology.Position()
            pos_instance.x.append(obj_pos.x)
            pos_instance.y.append(obj_pos.y)
            self.owl_instance.objects.append(pos_instance)
        for stack_pos, count in self.stacks.items():
            stack_instance = ontology.Position()
            stack_instance.x.append(stack_pos.x)
            stack_instance.y.append(stack_pos.y)
            self.owl_instance.active_stack.append(stack_instance)



parameters = {
    'steps': 4000,
}

# exp = ap.Experiment(WarehouseSimulation, parameters)
# exp = ap.Experiment(WarehouseSimulation)
# results = exp.run()

model = WarehouseSimulation(parameters)
model.sim_setup()
results = model.run()
model.end()

print("\n" + "="*65)
print("MULTI-AGENT WAREHOUSE SIMULATION - OVERVIEW")
print("="*65 + "\n")
print("INITIAL CONFIGURATION")
print(f"Warehouse size: {10}x{10}")
print(f"Number of robots: {5}")
print(f"Number of objects: {20}\n")
print("-"*65)
# print("EVENTS DURING THE SIMULATION")
# print("-"*65)
# if 'log' in results.reporters:
#     for log_entry in results.reporters['log'][0]:
#         print(f"{log_entry}")
# print("\n" + "="*65)
print("FINAL SUMMARY")
print("="*65)
print("SIMULATION END STATE")
print(f"Remaining objects: {results.reporters['remaining_objects'][0]}")
print(f"Status of stacks:")
for position, count in results.reporters['stacks'][0].items():
    print(f"  - Stack in {position}: {count} objects")
print("\nROBOT STATISTICS")
for robot_id, steps in results.reporters['robot_steps'][0].items():
    print(f"  - Robot {robot_id}:")
    print(f"    - Steps taken: {steps}")
total_steps = sum(results.reporters['robot_steps'][0].values())
avg_steps_per_robot = total_steps / 5
print("\nOVERALL STATISTICS")
print(f"Total steps taken by all robots: {total_steps}")
print(f"Average steps per robot: {avg_steps_per_robot:.2f}")
print(f"Objects initially: {20}")
print(f"Objects processed: {20 - results.reporters['remaining_objects'][0]}")
print(f"Objects left unprocessed: {results.reporters['remaining_objects'][0]}")
conflict_count = len([log for log in results.reporters['log'][0] if "Conflict detected" in log])
print(f"Conflicts detected: {conflict_count}")
print("\n" + "="*65)
print("END OF SIMULATION")
print("="*65)
ontology.save(file="output_ontology.owl", format="rdfxml")
