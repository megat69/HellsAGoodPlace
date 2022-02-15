from ursina import *
from ursina.shaders import lit_with_shadows_shader
from projectile import Projectile, ShotgunProjectile
from random import uniform

SLIDING_DURATION = 2
SHOTGUN_PROJECTILE_AMOUNT = 7


class Player(Entity):
    def __init__(self, settings, position=(0, 0, 0)):
        # Creating player
        self.crosshair = Entity(parent=camera.ui, model="quad", color=color.rgba(*settings.misc.crosshair_rgba), scale=.008)
        self.death_screen = Entity(parent=camera.ui, model="quad", color=color.rgba(255, 0, 0, 0), scale=4)
        self.death_screen.text_message = Text("You are dead.", origin=(0, 0), ignore_pause=True, color=color.rgba(255, 255, 255, 0))
        super().__init__(position=position)
        self.speed = 8
        self.height = 2
        self.camera_pivot = Entity(parent=self, y=self.height)
        self.light = Light(parent=self.camera_pivot)
        self.ground_light = Entity(parent=self, model="plane", texture="assets/ground_light.png")
        self.arms = Entity(parent=self.camera_pivot, model="assets/hand/hand", color=color.rgba(160, 0, 0, 100),
                           position=(.25, -.75, 1), rotation=(0, 270, -10), shader=lit_with_shadows_shader, always_on_top=True)
        self.collision_box = Entity(parent=self, model="cube", visible=False, collider="box", scale=(.5, self.height, .5))

        # Parenting camera to player
        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = clamp(settings.graphics.fov, 70, 103)
        mouse.locked = True
        self.mouse_sensitivity = Vec2(*settings.controls.sensitivity)

        # Initializing player attributes
        self.gravity = 1
        self.grounded = True
        self.jump_height = 2
        self.jump_up_duration = .5
        self.fall_after = .35
        self.jumping = False
        self.is_sliding = False
        self.sliding_direction = None
        self.air_time = 0
        self.projectile_cooldown = 0
        self.shotgun_countdown = 0
        self.dead = False
        self.can_fire = False

        # Making sure we don't fall through the ground if we start inside it
        if self.gravity:
            ray = raycast(self.world_position + (0, self.height, 0), self.down, ignore=(self, self.collision_box))
            if ray.hit:
                self.y = ray.world_point.y + self.height

        self._settings = settings

    def get_movement_direction(self):
        return Vec3(
            self.camera_pivot.forward * (held_keys[self._settings.bindings.forward] - held_keys[self._settings.bindings.backward])
            + self.camera_pivot.right * (held_keys[self._settings.bindings.right] - held_keys[self._settings.bindings.left])
        ).normalized()

    def update(self):
        if self.dead: return
        # Rotating the player
        self.camera_pivot.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]
        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -85, 85)

        # Resizing the camera pivot to the player height
        self.camera_pivot.y = self.height

        # Resizing the collision box
        self.collision_box.scale_y = self.height

        # Getting the player movement
        if self.is_sliding is False:
            old_y = self.y
            self.direction = self.get_movement_direction()

            # Detecting collisions
            feet_ray = raycast(self.position + Vec3(0, 0.5, 0), self.direction, ignore=(self, self.collision_box), distance=.5, debug=False)
            if not feet_ray.hit and self.is_sliding is False:  # If no collisions, moving the player
                self.position += self.direction * self.speed * (2 if held_keys[self._settings.bindings.sprint] else 1) * time.dt
                self.y = old_y
        else:
            if self.sliding_direction is not None:
                feet_ray = raycast(self.position + Vec3(0, 0.5, 0), self.sliding_direction, ignore=(self, self.collision_box), distance=1.5,
                                   debug=False)
                if feet_ray.hit:
                    for animation in self.animations:
                        animation.finish()
                    self.animate("height", 2, duration=SLIDING_DURATION * .05)
                    self.is_sliding = False
                    self.sliding_direction = None
                    camera.shake()

        # Updating the ground light
        self.ground_light.world_y = .01
        ground_light_distance = self.world_y - self.ground_light.world_y
        self.ground_light.scale = max(ground_light_distance, 1.5) * 2
        self.ground_light.color = color.rgba(255, 220, 220, min(round(255 / (ground_light_distance * 2)), 50) if ground_light_distance > 0 else 50)

        # Firing the auto-projectiles
        if held_keys["left mouse"] and self.projectile_cooldown <= 0 and not held_keys[self._settings.bindings.sprint] and self.can_fire:
            Projectile(self.arms.world_position + self.camera_pivot.forward * 2, self.camera_pivot.world_rotation, self.camera_pivot.forward)
            self.projectile_cooldown = .15
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= time.dt
        # Updating the shotgun countdown
        if self.shotgun_countdown > 0:
            self.shotgun_countdown -= time.dt

    def input(self, key):
        if key == self._settings.bindings.jump:
            self.jump()
        elif key == self._settings.bindings.slide:
            self.slide()
        elif key == "right mouse down" and self.shotgun_countdown <= 0 and self.can_fire and not held_keys[self._settings.bindings.sprint]:
            self.fire_shotgun()

    def fire_shotgun(self):
        old_rotation = self.camera_pivot.rotation
        for x in range(- SHOTGUN_PROJECTILE_AMOUNT // 2, SHOTGUN_PROJECTILE_AMOUNT // 2):
            for y in range(- SHOTGUN_PROJECTILE_AMOUNT // 2, SHOTGUN_PROJECTILE_AMOUNT // 2):
                self.camera_pivot.rotation_x -= x * uniform(3.5, 4.5)
                self.camera_pivot.rotation_y += y * uniform(3.5, 4.5)
                ShotgunProjectile(self.arms.world_position + self.camera_pivot.forward * 2,
                                  self.camera_pivot.world_rotation,
                                  self.camera_pivot.forward,
                                  self.world_position)
                self.camera_pivot.rotation = old_rotation
        self.shotgun_countdown = 1
        # Knockback
        if self.camera_pivot.rotation_x > 5:
            self.position -= self.forward * 6

    def slide(self):
        if self.is_sliding is False and self.grounded is True and held_keys[self._settings.bindings.forward]:
            self.is_sliding = True
            direction = self.get_movement_direction()
            self.sliding_direction = Vec3(direction.x, 0, direction.z) * self.speed * 2
            self.animate_position(self.position + self.sliding_direction,
                                  duration=SLIDING_DURATION + .2, curve=curve.out_expo)
            for animation in self.animations:
                invoke(animation.finish, delay = SLIDING_DURATION)
            self.animate("height", .75, duration=SLIDING_DURATION * .4)
            invoke(self.shake, delay = SLIDING_DURATION * .4)
            self.animate("height", 2, duration=SLIDING_DURATION * .1, delay = SLIDING_DURATION - SLIDING_DURATION * .1)
            invoke(setattr, self, "is_sliding", False, delay = SLIDING_DURATION)
            invoke(setattr, self, "sliding_direction", None, delay = SLIDING_DURATION)

    def jump(self):
        if self.grounded is False or self.is_sliding is True: return

        self.grounded = False
        self.animate_y(self.y + self.jump_height, duration=self.jump_up_duration, curve=curve.out_expo)
        invoke(self.start_fall, delay=self.jump_up_duration)

    def start_fall(self):
        self.y_animator.finish()
        self.animate_y(0, duration=self.jump_up_duration * .75, curve=curve.out_expo)
        invoke(self.land, delay=self.jump_up_duration * .74)

    def land(self):
        self.air_time = 0
        self.grounded = True

    def on_enable(self):
        mouse.locked = True
        self.crosshair.enabled = True

    def on_disable(self):
        mouse.locked = False
        self.crosshair.enabled = False
