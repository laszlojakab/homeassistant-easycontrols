from custom_components.easycontrols.const import VARIABLE_SERIAL_NUMBER
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator

coordinator = EasyControlsDataUpdateCoordinator(None, None)
i = 0
while not coordinator._variable_queue.empty():
    coordinator._update_next()

    if i == 3:
        coordinator.schedule_update(VARIABLE_SERIAL_NUMBER)

    i = i + 1
    if i == 100:
        break


# print(coordinator._variable_queue)

# from queue import PriorityQueue

# q = PriorityQueue()
# q.put((1, "a"))
# q.put((2, "c"))
# q.put((3, "b"))

# i = 0
# while not q.empty():
#     it = q.get()
#     print(it)

#     new_prio = it[0]
#     val = it[1]

#     if (new_prio < 3): new_prio = new_prio + 3
#     else: new_prio = new_prio - 3

#     q.put((new_prio, val))
#     i = i + 1
#     if i == 100:
#         break
