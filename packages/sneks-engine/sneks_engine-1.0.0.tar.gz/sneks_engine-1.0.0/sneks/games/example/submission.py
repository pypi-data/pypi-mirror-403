from sneks.engine.core.action import Action
from sneks.engine.core.direction import Direction
from sneks.engine.core.snek import Snek


class CustomSnek(Snek):
    def get_next_action(self) -> Action:
        # if there's food, head towards it
        if self.food:
            return self.get_direction_to_destination(
                self.get_closest_food()
            ).get_action()

        # move away from close obstacles
        close = [c for c in self.occupied if c.get_distance(self.head) < 10]
        sorted(close, key=lambda c: c.get_distance(self.head))
        if close:
            return sorted(
                ((d, self.look(d)) for d in Direction), key=lambda t: t[1], reverse=True
            )[0][0].get_action()

        # get back to not moving
        if self.get_bearing().x > 0:
            return Action.LEFT
        elif self.get_bearing().x < 0:
            return Action.RIGHT
        elif self.get_bearing().y > 0:
            return Action.DOWN
        elif self.get_bearing().y < 0:
            return Action.UP
        else:
            return Action.MAINTAIN
