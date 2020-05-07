import pygame
from constants import ARROW_COLOR_VEL, ARROW_TO_VEL_RATIO, ARROW_TO_ACC_RATIO, ARROW_MAX_LENGTH, TYPE_ACCEL, TYPE_VEL
import glm
from glm import vec2, vec3, vec4, mat4
import math

from celestial_entity import CelestialEntity

class TransientEntity():
    """
    Base class for Objects that will be drawn to screen but do not derive from pygame.sprite.Sprite
    """
    def __init__(self):
        self.dead = False
        self.world_offset = vec3(0)

    def update(self, dt):
        pass

    def draw(self, surface : pygame.Surface):
        pass

class IndicatorArrow(TransientEntity):

    def __init__(self, start, parent : CelestialEntity = None, **kwargs):
        super().__init__()

        self.parent : CelestialObject = parent
        
        if isinstance(start, tuple):
            self.start = vec3(start[0], start[1], 0)
        elif isinstance(start, vec3):
            self.start = start

        self.end = vec3(self.start.x+1, self.start.y+1, 0)

        self.color = kwargs.pop("color", ARROW_COLOR_VEL)
        self.thickness = kwargs.pop("thickness", 2)
        # self.thickness = kwargs.pop("thickness", ARROW_HALF_THICKNESS)
        # self.cap_angle = kwargs.pop("cap_angle", ARROW_CAP_ANGLE)
        # self.cap_length = kwargs.pop("cap_length", ARROW_CAP_LENGTH)
        self.indcator_type = kwargs.pop("indicator_type", None)

        self.component = vec3(0)
        self.length = 0.0
        self.angle = 0.0

    @property
    def arrow_end(self):
        return self.end

    @arrow_end.setter
    def arrow_end(self, e):
        # print(f"Updating arrow endpoint {e}")
        self.end = vec3(e[0], e[1], 0)
        self.__limit_length()

    def __limit_length(self):
        length = glm.distance(self.start, self.end)
        if length > ARROW_MAX_LENGTH:
            self.end = vec3((self.end.x - self.start.x) / length * ARROW_MAX_LENGTH + self.start.x, 
                        (self.end.y - self.start.y) / length * ARROW_MAX_LENGTH + self.start.y,
                        0)
        self.length = glm.distance(self.start, self.end)

    @property
    def velocity_component(self) -> vec3:
        self.angle = self.__calc_angle()
        v = vec3(self.length * math.cos(self.angle), self.length * math.sin(self.angle), 0)  
        return v

    def __calc_angle(self):
        angle = math.atan2(self.start.y - self.end.y, self.end.x - self.start.x)
        return angle

    def __recalculate_for_celestial(self):
        if self.parent:
            if isinstance(self.parent, CelestialEntity):
                origin = self.parent.position
                self.start = vec3(origin.x, origin.y, 0)

                endx = 0
                endy = 0
                if self.indcator_type == TYPE_VEL:
                    endx = origin.x+self.parent.velocity.x/ARROW_TO_VEL_RATIO
                    endy = origin.y+self.parent.velocity.y/ARROW_TO_VEL_RATIO
                elif self.indcator_type == TYPE_ACCEL:
                    endx = origin.x+self.parent.acceleration.x/ARROW_TO_ACC_RATIO
                    endy = origin.y+self.parent.acceleration.y/ARROW_TO_ACC_RATIO

                self.end = vec3(endx, endy, 0)

    def update(self, dt):
        super().update(dt)
        
        # self.__update_angle() # TODO: This recalculation might not be necessary here
        
        self.__recalculate_for_celestial()

        self.start += self.world_offset
        self.end += self.world_offset

    def draw(self, surface : pygame.Surface):
        super().draw(surface)
        # Draw the arrow line
        pygame.draw.line(surface, self.color, (self.start.x, self.start.y), (self.end.x, self.end.y), self.thickness)    

        # Draw the arrow head
        arrow_points = self.__generate_arrowhead_method1(3)
        pygame.draw.polygon(surface, self.color, arrow_points, 0)

    def __arrow_head(self):
        arrow_head = [
            vec2(0, 2), vec2(-1, -2), vec2(1, -2)
        ]
        return arrow_head

    def __generate_arrowhead_method1(self, scale) -> []:
        arrow_points = []
        z = vec3(0, 0, 1)
        rads =  glm.radians(270) - self.__calc_angle()
        for p in self.__arrow_head():
            p = vec4(p.x, p.y, 0, 0)
            p = p*scale
            M = glm.rotate(mat4(1), rads, z)
            p = M*p
            p = vec2(p.x, p.y)
            p = p+vec2(self.end.x, self.end.y)
            arrow_points.append(p)

        return arrow_points

    def __generate_arrowhead_method2(self, scale) -> []:
        arrow_points = []
        rads = self.__calc_angle() + glm.radians(90)
        degs = glm.degrees(rads)
        for p in self.__arrow_head():
            p = p*scale
            p = p.rotate(-degs)
            p = p+pygame.Vector2(self.end.x, self.end.y)
            arrow_points.append(p)

        return arrow_points