import pygame
from usercontrol import UserControlGroup, Button, ToggleButton

class CelestialSceneGui():
    PLAY_PAUSE_BUTTON = "playpause"
    CREATE_PLANET_BUTTON = "createplanet"

    BUTTON_BG_COLOR = (0, 100, 200)
    BUTTON_FG_COLOR = (255, 255, 255)

    def __init__(self, controls_group = None, **kwargs):
        print(f"Controls group: {controls_group}")

        if controls_group == None:
            self.controls_group = UserControlGroup()
        else:
            self.controls_group = controls_group

        self.__scene_control_buttons = {}

        self.button_bg_clr = kwargs.pop("bg_color", self.BUTTON_BG_COLOR)
        self.button_fg_clr = kwargs.pop("fg_color", self.BUTTON_FG_COLOR)
        self.button_size = kwargs.pop("size", (50, 50))

    def build_control_panel(self, pos):
        play_pause_pos = [pos[0], pos[1]]
        self.__build_play_pause_button(play_pause_pos)
        

        return self.__scene_control_buttons

    def __build_play_pause_button(self, pos):
        play_btn_img = pygame.image.load("resources\images\play_button.png")
        pause_btn_img = pygame.image.load("resources\images\pause_button.png")

        fn1 = lambda: print("Function 1")
        fn2 = lambda: print("Function 2")
        btn = ToggleButton(self.controls_group, self.PLAY_PAUSE_BUTTON, function1 = fn1, function2 = fn2, width = 50, height = 50)
        btn.x = pos[0]
        btn.y = pos[1]
        print(f"Created ToggleButton @ {btn.x} {btn.y}")
        self.__scene_control_buttons[self.PLAY_PAUSE_BUTTON] = btn

    # def __draw_play_button(self, surface):
    #     surface.fill(self.button_bg_clr)
    #     scale = 25
    #     play_tri_points = [
    #         pygame.Vector2(-1, 1), pygame.Vector2(1, 0), pygame.Vector2(-1, -1)
    #     ]
    #     for p in play_tri_points:
    #         p = p*scale
    #         p = p+12
    #     pygame.draw.polygon(surface, self.button_fg_clr, play_tri_points)

    # def __draw_pause_button(self, surface):
    #     surface.fill(self.button_bg_clr)
    #     scale = 10
    #     size = pygame.Vector2(1, 2)*scale
    #     play_rects = [
    #         pygame.Rect(0, 0, size),
    #         pygame.Rect(0, 0, size)
    #     ]
    #     for r in play_rects:
    #         pygame.draw.rect(surface, self.button_fg_clr, r)

    def _toggle_play_pause_button_image(self):
        pass

    def __build_create_planet_button(self):
        pass

    def _toggle_create_planet_button_image(self):
        pass