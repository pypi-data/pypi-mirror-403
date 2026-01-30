from time import sleep

from approxeng.input.controllers import find_matching_controllers, ControllerRequirement
from approxeng.input.selectbinder import bind_controllers


class PiHutController:
    """
    Reads continuous input from a connected controller via approxeng.input.
    Uses controller.stream to yield joystick and button states.
    """

    def __init__(self, deadzone=0.25):
        self.deadzone = deadzone
        self._discovery = self._discover_controller()
        self._unbind = bind_controllers(self._discovery, print_events=False)
        self._stream = self._discovery.controller.stream

    def _discover_controller(self):
        discovery = None
        while discovery is None:
            try:
                discovery = find_matching_controllers(ControllerRequirement(
                    require_snames=['lx', 'ly', 'rx', 'ry']))[0]
            except IOError:
                print("Waiting for controller...")
                sleep(0.5)
        return discovery

    def close(self):
        if self._unbind:
            self._unbind()

    def stream(self):
        """
        Generator yielding controller input continuously.
        Each iteration yields a dictionary with all relevant control states.
        """
        for state in self._stream['lx', 'ly', 'rx', 'ry']:
            lx = self._apply_deadzone(state[0])
            ly = self._apply_deadzone(state[1])
            rx = self._apply_deadzone(state[2])
            ry = self._apply_deadzone(state[3])

            yield {
                'lx': lx,
                'ly': ly,
                'rx': rx,
                'ry': ry,
            }

    def _apply_deadzone(self, value):
        return 0.0 if abs(value) < self.deadzone else value
