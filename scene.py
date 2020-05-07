from glm import vec2, vec3
import pygame

from constants import BACKGROUND_COLOR, CAM_MOVE_SPEED, CAM_ZOOM_AMOUNT, ZOOM_MIN, ZOOM_MAX, TYPE_ACCEL, TYPE_VEL, SCREEN_WIDTH
# from objects import CelestialObject, SpriteEntity, TransientDrawEntity, TextObject, VelocityArrow
# from objects import TransientDrawEntity, TextObject, VelocityArrow
# from objects import TextObject
from usercontrol import UserControlGroup, Label, ToggleButton
from celestial_scene_gui import CelestialSceneGui
from transient_entity import TransientEntity, IndicatorArrow
from celestial_entity import CelestialEntity, PlanetEntity
from containers import CelestialSpriteGroup

class Camera():
    def __init__(self):
        self.fov = 90
        self.position = vec3(0)
        self.rotation = vec3(0)

    def shift(self, v : vec3):
        self.position += v

class Scene():
    def __init__(self, app):
        self.app = app

        self.bg_color = (0,0,0)
        self.content = pygame.sprite.RenderUpdates()
        self.camera = Camera()

    def move_cam_left(self):
        self.camera.shift(vec3(CAM_MOVE_SPEED, 0, 0))

    def move_cam_right(self):
        self.camera.shift(vec3(-CAM_MOVE_SPEED, 0, 0))

    def move_cam_up(self):
        self.camera.shift(vec3(0, CAM_MOVE_SPEED, 0))

    def move_cam_down(self):
        self.camera.shift(vec3(0, -CAM_MOVE_SPEED, 0))

    def move_cam_out(self):
        if (self.camera.position.z > ZOOM_MIN):
            self.camera.shift(vec3(0, 0, -CAM_ZOOM_AMOUNT))
        else:
            print("Can't zoom out further")

    def move_cam_in(self):
        if (self.camera.position.z < ZOOM_MAX):
            self.camera.shift(vec3(0, 0, CAM_ZOOM_AMOUNT))
        else:
            print("Can't zoom in further")

    def camera_front(self):
        self.camera.position.x = 100
        self.camera.position.y = 0
        self.camera.position.z = 0
        self.camera.rotation.y = 90

    def camera_normal(self):
        self.camera.position = vec3(0)
        self.camera.rotation = vec3(0)

    def update(self, delta_time):
        # Update all sprites in the scene.content
        self.content.update(delta_time)

    def draw(self, surface : pygame.Surface):
        # Draw all sprites in scene.content
        surface.fill(self.bg_color)

        dirty_rects = self.content.draw(surface)  # TODO: handle dirty rects back up to App.draw()

class CelestialScene(Scene):
    """
    Celestial Scene Class
    - Handles graphical elements
    """
    def __init__(self, app):
        super().__init__(app)

        self.celest_objs = CelestialSpriteGroup()
        self.transient_objs = []
        
        self.controls = UserControlGroup()
        self.gui = CelestialSceneGui(self.controls)
        self.gui.build_control_panel((300, 20))

        # self.__camera_pos_disp = TextObject('X: 0, Y: 0, Z: 0', self.app.font, (0,0,0))
        self.__camera_pos_disp = Label(self.controls, "camera_pos_label", text = 'X: 0000.0, Y: 0000.0, Z: 0000.0', font = self.app.font)
        self.__camera_pos_disp.x = 5
        self.__camera_pos_disp.y = 5

        self.bg_color = BACKGROUND_COLOR

        for c in self.controls:
            print(f"Control of type: {type(c)}")

    def add_new_celestial(self, new_celestial):
        # New celestial instance with world_offset
        ctr = new_celestial.rect.center
        world_ctr = (ctr[0] + int(-self.camera.position.x), ctr[1] + int(-self.camera.position.y))
        new_celestial.position = world_ctr
        
        # Set the group to the celestial
        new_celestial.neighbours = self.celest_objs

        # Add to sprite.Group() for processing
        self.celest_objs.add(new_celestial)
        
        # Add to scene sprite.Group() for drawing
        self.content.add(new_celestial)

        # Add vector arrows to for celestial
        arr_accel = IndicatorArrow(new_celestial.position, new_celestial, color=(200,0,0), indicator_type=TYPE_ACCEL, thickness=1)
        arr_vel = IndicatorArrow(new_celestial.position, new_celestial, color=(0,70,170), indicator_type=TYPE_VEL, thickness=1)

        self.transient_objs.append(arr_accel)
        self.transient_objs.append(arr_vel)

        return new_celestial

    def kill_all_objects(self):
        """
        Private function to kill all objects
        """
        # Iterate and call pygame.sprite.Sprite kill() function to remove from any pygame.sprite.Groups()
        for o in self.celest_objs:
            o.kill()
        
        # Clear all transients
        self.transient_objs.clear()

        print(f"Killed all objects: Celestials: {len(self.celest_objs)}, Transients: {len(self.transient_objs)}")

    def update(self, delta_time):
        """
        Update Scene
        """
        super().update(delta_time)

        # Update Camera Position Label UserControl
        cam_text = f"X: {self.camera.position.x}, Y: {self.camera.position.y}, Z: {self.camera.position.z}"
        self.__camera_pos_disp.text = cam_text

        # Call update() method of all sprites in the sprite.Group()
        self.celest_objs.update(delta_time)

        # Call update() method of all user controls in the 'controls' group
        self.controls.update(delta_time)
        for c in self.controls:
            if isinstance(c, ToggleButton):
                print(f"Updating control of type: {type(c)}")

        # Iterate sprite group
        for o in self.celest_objs:
            # Update world offset for all items
            if isinstance(o, CelestialEntity):
                o.world_offset = self.camera.position
                o.world_rotation = self.camera.rotation

                # Reset 'just_calcd' variable for next frame
                o.force_just_calcd = False

        # Iterate transient non-sprite graphical objects list (in reverse to protect when removing)
        for t in reversed(self.transient_objs):
            # Update world offset, call update() and remove expired Transients
            if isinstance(t, TransientEntity):
                t.world_offset = self.camera.position
                t.update(delta_time)
                if t.dead:
                    self.transient_objs.remove(t)

    def draw(self, surface : pygame.Surface):
        """
        Draw function
        - Handles drawing any objects that are not automatically drawn through sprite.Group()s
        """
        # Call super() draw() function to draw scene.content
        super().draw(surface)

        # Iterate all Transient objects and call .draw() func
        for t in self.transient_objs:
            if isinstance(t, TransientEntity):
                t.draw(surface)

        # Draw all controls in the 'controls' group
        self.controls.draw(surface)

    def __create_gui_controls(self):
        play_pause_img = pygame.Surface(50, 50)
        
        play_pause_btn = None
        create_planet_btn = None
        select_celestial_btn = None
        move_camera_btn = None
        rotate_camera_btn = None
