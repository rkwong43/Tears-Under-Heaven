from src.entities.effects.effect import Effect
from src.utils import config

"""Represents a charge up effect for rail guns. Has 12 frames."""


class ChargeUp(Effect):

    """Constructor to make the explosion.

    :param x: x coordinate of explosion
    :type x: int
    :param y: y coordinate of explosion
    :type y: int
    :param entity_id: ID representing what effect it is
    :type entity_id: EntityID
    """

    def __init__(self, x, y, entity_id):
        super().__init__(x, y, entity_id)
        self.max_frame = 16 * int(config.game_fps / 30)


