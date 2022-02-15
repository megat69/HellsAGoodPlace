from ursina import *
from player import Player
from monster import Skull
from intro import IntroDiamond
import json
from random import randint
import os

# Loading the settings
with open("settings.json", "r", encoding="utf-8") as settings_file:
    class SETTINGS:
        SETTINGS_AS_JSON = json.load(settings_file)

    def add_attrs_to_settings(cls, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(cls, key, SETTINGS())
                add_attrs_to_settings(getattr(cls, key), value)
            else:
                setattr(cls, key, value)
    add_attrs_to_settings(SETTINGS, SETTINGS.SETTINGS_AS_JSON)
    del add_attrs_to_settings

# Creating the window
app = Ursina(fullscreen=SETTINGS.video.fullscreen, vsync=SETTINGS.video.vsync)
window.exit_button.visible = False
if SETTINGS.misc.show_FPS_counter is True:
    window.fps_counter.color = color.lime
    window.fps_counter.y += 0.015
else:
    window.fps_counter.visible = False
window.exit_button.disabled = True
application.development_mode = False

# Caps the framerate if wanted
if SETTINGS.video.framerate_limiter is not None:
    from panda3d.core import ClockObject
    globalClock.setMode(ClockObject.MLimited)
    globalClock.setFrameRate(SETTINGS.video.framerate_limiter)

# Creating the player
player = Player(SETTINGS, position=(-4, 0, -4))

# Loading every blood pool texture
for texture in os.listdir("assets/blood_pools/"):
    load_texture("assets/blood_pools/" + texture)
# Loading projectile model
load_model("assets/projectile")
# Loading music
music = Audio("assets/sfx/music.mp3", autoplay=False, loop=True)

# Defines whether we are in the intro
in_intro = True

# Time spent
time_spent = 0
spawn_time = 0
spawn_time_resetter = 15
spawn_time_reset_value = 2

def update():
    global in_intro
    if in_intro:
        if player.collision_box.intersects(intro_diamond):
            print("Launching game")
            music.play()
            arena_floor.animate_color(arena_color, duration=1)
            destroy(intro_diamond.ground_cast)
            destroy(intro_diamond)
            in_intro = False
            player.can_fire = True
    else:
        global spawn_time
        global time_spent
        global spawn_time_resetter
        global spawn_time_reset_value
        spawn_time -= time.dt
        time_spent += time.dt
        spawn_time_resetter -= time.dt

        if spawn_time <= 0 and player.dead is False:
            Skull(player, (randint(-30, 30), randint(2, 3), randint(-30, 30)), SETTINGS)
            spawn_time = spawn_time_reset_value
        if spawn_time_resetter <= 0 and spawn_time_reset_value > 0.8:
            spawn_time_reset_value -= 0.05
            spawn_time_resetter = 15

        # Stopping music if player is dead
        if player.dead and music.playing:
            music.fade_out()


if __name__ == '__main__':
    arena_color = color.rgb(180, 160, 160)
    arena_floor = Entity(model="plane", collider="plane", scale=64, texture="assets/arena.png", color=color.rgb(60, 40, 40))
    arena_borders = Entity(model="assets/cylinder_arena_collider", scale=28, collider="mesh", visible=False)
    sky = Sky(texture=None, color=color.rgb(20, 10, 10))

    intro_diamond = IntroDiamond()

    from pixelated_shader import PixelatedShader
    camera.shader = PixelatedShader
    app.run()
