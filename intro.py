from ursina import *
from ursina.shaders import matcap_shader


class IntroDiamond(Entity):
    def __init__(self):
        super().__init__(model="assets/projectile", color=color.hsv(183, .91, 1), scale=1.2, y=2, shader=matcap_shader, collider="box")
        self.ground_cast = Entity(model="plane", y=.099, texture="assets/arena.png", color=color.rgb(0, 242, 255), scale=2)
        self.y_movements_sequence = Sequence(
            Func(self.animate_position, (self.x, 2.8, self.z), duration=2, curve=curve.linear),
            Func(self.animate_color, color.hsv(183, .91, .88), duration=2, curve=curve.linear),
            Func(self.ground_cast.animate_scale, 2.8, duration=2, curve=curve.linear),
            2.1,
            Func(self.animate_position, (self.x, 2, self.z), duration=2, curve=curve.linear),
            Func(self.animate_color, color.hsv(183, .91, 1), duration=2, curve=curve.linear),
            Func(self.ground_cast.animate_scale, 2, duration=2, curve=curve.linear),
            2.1,
            loop=True
        )
        self.y_movements_sequence.start()
