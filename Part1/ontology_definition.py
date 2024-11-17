from owlready2 import *

onto = get_ontology("http://example.org/warehouse_simulation_ontology.owl")

with onto:
    class Position(Thing):
        pass

    class Robot(Thing):
        pass

    class WarehouseSimulation(Thing):
        pass

    class x(DataProperty):
        domain = [Position]
        range = [int]

    class y(DataProperty):
        domain = [Position]
        range = [int]

    class facing_direction(DataProperty):
        domain = [Robot]
        range = [str]

    class is_carrying_object(DataProperty):
        domain = [Robot]
        range = [bool]

    class is_active(DataProperty):
        domain = [Robot]
        range = [bool]

    class steps(DataProperty):
        domain = [Robot]
        range = [int]

    class rows(DataProperty):
        domain = [WarehouseSimulation]
        range = [int]

    class cols(DataProperty):
        domain = [WarehouseSimulation]
        range = [int]

    class num_objects(DataProperty):
        domain = [WarehouseSimulation]
        range = [int]

    class num_robots(DataProperty):
        domain = [WarehouseSimulation]
        range = [int]

    class has_position(ObjectProperty):
        domain = [Robot, WarehouseSimulation]
        range = [Position]

    class occupied_positions(ObjectProperty):
        domain = [WarehouseSimulation]
        range = [Position]

    class reserved_objects(ObjectProperty):
        domain = [WarehouseSimulation]
        range = [Position]

    class objects(ObjectProperty):
        domain = [WarehouseSimulation]
        range = [Position]

    class active_stack(ObjectProperty):
        domain = [WarehouseSimulation]
        range = [Position]

    class target_object(ObjectProperty):
        domain = [Robot]
        range = [Position]

    class target_stack(ObjectProperty):
        domain = [Robot]
        range = [Position]

onto.save(file="ontology.owl", format="rdfxml")
