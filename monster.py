from ursina import *
from random import uniform, randint
import os
RANDOMNESS = .01
DEATH_DURATION = .2
monsters_killed = 0
blood_pools = []


def blood_cubes_particles(position):
    for x in (-.2, .2):
        for z in (-.2, .2):
            BloodCube(position, Vec3(x, 0, z))


class BloodCube(Entity):
    def __init__(self, position, vector):
        super().__init__(position=position, model="cube", scale=.008, color=color.red)
        self.animate_position(self.position + vector + Vec3(0, .7, 0), duration=.8)
        self.animate_position(self.position + vector + Vec3(0, -3, 0), duration=.5, delay=.8)

    def update(self):
        if self.world_y <= 0:
            destroy(self)


class Skull(Entity):
    def __init__(self, player, position, settings):
        self.colors = (color.rgba(84, 122, 106, 230), color.rgba(245, 193, 64, 245))
        self.current_color = 0
        super().__init__(model="assets/skull/skull.obj", texture="assets/skull/skull_texture.png", position=position,
                         scale=.02, color=self.colors[0], collider="box")
        self.player = player
        self.health = 2
        self.active = False
        self._settings = settings

        # Randomizing position again if too close to the player
        while distance(self, self.player) < 25:
            self.world_position = (randint(-30, 30), randint(2, 3), randint(-30, 30))
        self.active = True

    def update(self):
        global monsters_killed
        # Checking health
        if self.health <= 0:
            self.animate_position((self.x, -3, self.z), duration=.2, curve=curve.in_sine)
            destroy(self, delay=.21)
            monsters_killed += 1

            # --- Creating blood pool ---
            # Choosing a random blood pool
            chosen_pool_number = randint(1, len(os.listdir("assets/blood_pools/")))
            # Applying the blood pool
            if self._settings.performance.max_blood_pools_number is not None \
                    and len(blood_pools) >= self._settings.performance.max_blood_pools_number:
                destroy(blood_pools[0])
                blood_pools.pop(0)
            blood_pools.append(Entity(model="plane", texture=f"assets/blood_pools/blood_pool_{chosen_pool_number}.png",
                                      position=(self.x, monsters_killed * 10**(-10), self.z)))
            # Spawning four little cubes flying off after death
            blood_cubes_particles(self.position)

        # Changing to color 2 if player is too close
        if distance(self, self.player) < 8:
            if self.current_color == 0:
                self.animate_color(self.colors[1])
                self.current_color = 1
        else:
            if self.current_color == 1:
                self.animate_color(self.colors[0])
                self.current_color = 0

        # Movement towards player
        self.look_at((self.player.x, self.player.y + (self.player.height / 2), self.player.z))
        self.position += (self.forward + \
                          Vec3(
                              uniform(-RANDOMNESS, RANDOMNESS),
                              uniform(-RANDOMNESS, RANDOMNESS),
                              uniform(-RANDOMNESS, RANDOMNESS)
                          )) * 325 * time.dt

        # Killing player if intersecting with it
        if self.intersects(self.player.collision_box) and self.active:
            self.player.dead = True
            self.player.camera_pivot.animate_position((0, 0.5, 0), duration=DEATH_DURATION, curve=curve.out_expo)
            self.player.death_screen.animate_color(color.rgba(255, 0, 0, 180), duration=DEATH_DURATION)
            self.player.death_screen.text_message.animate_color(color.rgba(255, 255, 255, 255), duration=DEATH_DURATION * 4)
