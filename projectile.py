from ursina import *
PROJECTILE_SPEED = 20
from monster import Skull, blood_cubes_particles

class Projectile(Entity):
    def __init__(self, position, rotation, direction, damage=1):
        super().__init__(model="assets/projectile", color=color.rgba(255, 0, 0, 150),
                         position=position, roation=rotation + Vec3(90, 0, 0), scale=.2)
        self.direction = direction
        self.last_position = self.position
        self.active = True
        self.damage = damage

    def default_update(self):
        ray = raycast(self.position, self.direction, ignore=(self,), distance=.5)
        if ray.hit and self.active:
            try:
                self.animate_color(color.rgba(255, 0, 0, 0), duration=.3)
            except Exception:
                pass
            destroy(self, delay=.5)
            self.active = False

            # Damages the entity if necessary if necessary
            if isinstance(ray.entity, Skull):
                ray.entity.health -= self.damage
                blood_cubes_particles(self.position)

        self.position += self.direction * time.dt * PROJECTILE_SPEED

        if distance(Vec3(0, 0, 0), self.position) > 50: destroy(self)

    def update(self):
        self.default_update()


class ShotgunProjectile(Projectile):
    def __init__(self, position, rotation, direction, starting_pos, damage=1):
        super().__init__(position, rotation, direction, damage)
        self.starting_pos = starting_pos
        self.animate_color(color.rgba(255, 0, 0, 0), duration=.5)

    def update(self):
        self.default_update()

        # Reducing damage based off starting point distance
        try:
            self.damage = 8 - distance(self, self.starting_pos)
        except Exception:
            pass

        if self.damage <= 0:
            self.active = False
