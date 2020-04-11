import random

from src.entities.ships.waypoint import Waypoint
from src.model.model import Model
from src.utils import config, enemy_generator
from src.utils.ids.difficulty_id import DifficultyID
from src.utils.ids.effect_id import EffectID
from src.utils.ids.enemy_id import EnemyID
from src.utils.ids.game_id import GameID
from src.utils.ids.gamemode_id import GameModeID
from src.utils.ids.player_id import PlayerID

"""Represents the model that handles displaying weapons or enemies in a gallery type menu.
"""


class MenuModel(Model):
    """Initializes the model.
    """

    def __init__(self):
        super().__init__(DifficultyID.EASY, GameModeID.CLASSIC)
        random.seed()
        self._player_ship.x = config.display_width
        self._play = False
        # If a weapon or enemy is being showcased
        self._showcase_weapon = False
        self._props = []

    """Prepares another showcase.
    
    :param entity_type: Type of showcase (player, enemy, weapon)
    :type entity_type: GameID
    :param entity_id: ID of the specified type
    :type entity_id: Enum
    """

    def showcase(self, entity_type, entity_id):
        self._showcase_weapon = False
        if entity_type == GameID.SHIP:
            self.spawn_player(entity_id)
        elif entity_type == GameID.ENEMY:
            self._spawn_ship(entity_id)
        else:
            self._showcase_weapon = True
            self.switch_weapon(entity_id)

    """Resets the position of props.
    """

    def reset_showcase(self):
        self._showcase_weapon = False
        for ship in self._props:
            ship.y += 2 * config.display_height

    """Sets the current playing state.
    
    :param start: True if playing, false otherwise
    :type start: bool
    """

    def set_play(self, start):
        self._play = start

    """Represents a tick in the game. Handles reloads and moves all projectiles and updates the AI module to
    move enemies. Also rotates enemies to face the player.
    """

    def tick(self):
        # Moves all projectiles
        for projectile in self.friendly_projectiles + self.enemy_projectiles:
            projectile.move()
        # Has enemies immediately fire when ready
        for ship in self.enemy_ships + self.friendly_ships + self._props:
            ship.move()
            ship.ticks += 1
            if ship.ticks == ship.fire_rate:
                ship.ticks = 0
                if ship.ready_to_fire:
                    self.play_sound(ship.projectile_type)
                    if ship in self.friendly_ships:
                        ship.fire(self.find_closest_target(ship, self.enemy_ships), self.friendly_projectiles)
                    else:
                        ship.fire(self._player_ship, self.enemy_projectiles)
        # Reloads the player's weapon depending on its fire speed
        if self._showcase_weapon:
            if self._reload < self._reload_time:
                self._reload += 1
            elif self._reload == self._reload_time:
                self._projectile_generator()
                self._reload = 0
        # Checks collisions between projectiles and ships
        self._remove_off_screen_objects()
        for ship in self.enemy_ships + self.friendly_ships + self._props:
            ship.is_damaged = False
        self._player_ship.is_damaged = False
        self._check_collisions()

    """Switches the player's weapon to the given type.

    :param weapon: weapon type
    :type weapon: EntityID
    """

    def switch_weapon(self, weapon):
        super().switch_weapon(weapon)
        self._player_stats["DAMAGE"] = 0
        self._player_ship.x = x_pos = config.display_width / 4
        self._player_ship.y = config.display_height * .75
        x_pos -= config.ship_size
        for i in range(3):
            mandible = enemy_generator.generate_enemy(EnemyID.MANDIBLE, x_pos + (i * config.ship_size),
                                                      config.display_height / 3)
            mandible.fire_rate = 0
            self._props.append(mandible)

    """Spawns a ship and places it in a predetermined position.

    :param entity_id: ID of ship to spawn
    :type entity_id: EntityID
    """

    def _spawn_ship(self, entity_id):
        self._player_ship.x = config.display_width / 4
        self._player_ship.y = config.display_height * .75
        x_pos = config.display_width / 4

        if entity_id in [EnemyID.ARBITRATOR, EnemyID.TERMINUS, EnemyID.JUDICATOR]:
            ship = enemy_generator.generate_enemy(entity_id, x_pos - (config.ship_size // 4),
                                                  config.display_height / 3, effects=self.effects)
        elif entity_id in [EnemyID.MOTHERSHIP, EnemyID.DESPOILER]:
            ship = enemy_generator.generate_enemy(entity_id, x_pos - (config.ship_size // 2),
                                                  config.display_height / 3, effects=self.effects)
        elif entity_id in EnemyID:
            ship = enemy_generator.generate_enemy(entity_id, x_pos, config.display_height / 3)
        else:
            return
        ship.projectile_damage = 0
        self._props.append(ship)

    """Renders the player ship.
    :param entity_id: ID of player ship
    :type entity_id: EntityID
    :param x: x position
    :type x: int
    :param y: y position
    :type y: int
    """

    def spawn_player(self, entity_id, x=config.display_width / 4, y=config.display_height / 2):
        self._player_ship.x = x
        self._player_ship.y = y
        self._player_ship.entity_id = entity_id

    """Checks for any projectile collisions between ships and ship collisions. If the ship is destroyed, adds an
       explosion effect to the effects list.
       """

    def _check_collisions(self):
        # Checks friendly projectiles vs. enemy ships
        self.friendly_projectiles[:] = [projectile for projectile in self.friendly_projectiles
                                        if not self._check_if_hit(projectile, self.enemy_ships + self._props,
                                                                  EffectID.BLUE_EXPLOSION)]
        # Checks enemy projectiles vs. friendly ships
        self.enemy_projectiles[:] = [projectile for projectile in self.enemy_projectiles
                                     if not self._check_if_hit(projectile, self.friendly_ships + [self._player_ship],
                                                               EffectID.RED_EXPLOSION)]

    """Removes all off screen objects such as projectiles or ships.
        """

    def _remove_off_screen_objects(self):
        self.friendly_projectiles[:] = [projectile for projectile in self.friendly_projectiles
                                        if not self._is_off_screen(projectile)]
        self.enemy_projectiles[:] = [projectile for projectile in self.enemy_projectiles
                                     if not self._is_off_screen(projectile)]
        self.friendly_ships[:] = [ship for ship in self.friendly_ships
                                  if not self._is_off_screen(ship)]
        self.enemy_ships[:] = [ship for ship in self.enemy_ships
                               if not self._is_off_screen(ship)]

    """Checks if the given entity is off screen.

   :param entity: entity to check
   :type entity: Entity
   """

    def _is_off_screen(self, entity):
        size = entity.size // 2
        center = (entity.x + size, entity.y + size)
        # if off screen:
        x_off = center[0] > config.display_width + size or center[0] < -size
        y_off = center[1] > config.display_height + size or center[1] < -size
        return x_off or y_off

    """Spawns random ships and has them move around and shoot.
    """

    def spawn_ships(self):
        # ~18% chance of spawning ships randomly
        if random.randint(1, 6) == 6:
            random_ship_quantity = random.randint(1, 6)
            x_posns = []
            for _ in range(random_ship_quantity):
                random_speed = random.randint(5, 15)
                rand_x = 0
                good_x = False
                while not good_x:
                    rand_x = random.randint(0, config.display_width - config.ship_size)
                    try:
                        for posn in x_posns:
                            if posn - config.ship_size < rand_x < posn + config.ship_size:
                                raise ValueError
                    except ValueError:
                        continue
                    good_x = True
                ship_id = PlayerID.CITADEL
                if random.randint(1, 4) == 4:
                    ship_id = PlayerID.AEGIS
                ship = enemy_generator.generate_enemy(ship_id,
                                                      rand_x,
                                                      config.display_height - config.ship_size,
                                                      speed=random_speed)
                x_posns.append(rand_x)
                ship.set_waypoint(wp=Waypoint(rand_x, -config.ship_size), fire_at=True)
                # They do not shoot
                ship.ready_to_fire = False
                self.friendly_ships.append(ship)

    """Returns all ships and props.
    """

    def get_ships(self):
        return self.enemy_ships + self.friendly_ships + self._props
