import pygame
import glm
from glm import vec2, vec3, vec4, mat4
import math
from constants import PLANET_DEFAULT_DENSITY, PLANET_MIN_RADIUS, PLANET_MAX_RADIUS, PLANET_COLOR, ARROW_TO_VEL_RATIO, DELTA_T

class CelestialEntity(pygame.sprite.Sprite):
    """
    Base class for celestial objects 
    - Entity appearance (sprite)
    - Radius, Mass, Force, Acceleration, Velocity, Position
    - 
    """
    def __init__(self, center, **kwargs):
        super().__init__()

        self.__id = '0'

        self.neighbours = pygame.sprite.Group()

        self.density = kwargs.pop("density", 0.005)
        
        self.__radius = self._correct_radius(kwargs.pop("radius", 0))
        self.mass = self.density*(4/3*math.pi*(self.__radius**3)) 
        
        self.F = vec3(0)
        self.acc = vec3(0)
        self.vel = vec3(0)
        self.pos = vec3(center[0], center[1], 0)

        self.world_offset = vec3(0)
        self.world_rotation = vec3(0)

        self.force_just_calcd = False  

    ###
    ### Properties
    ###

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def radius(self):
        """
        Getter for radius
        """
        return self.__radius

    @radius.setter
    def radius(self, r):
        """
        Setter for radius
        - Resets image, rect, mass and radius
        """
        r = self._correct_radius(r)
        size = 2*r+2        
        surf = pygame.Surface([size]*2, pygame.SRCALPHA)
        pygame.draw.circle(surf, PLANET_COLOR, [r]*2, r)
        self.image = surf.convert_alpha()
        self.rect = self.image.get_rect(center=self.rect.center)            
        self.mass = self.density*r**3
        self.__radius = r

        # Store original image copy to prevent scale transform artifacts
        self.__zero_image = self.image.convert_alpha()

    @property
    def acceleration(self):
        return self.acc

    @property
    def velocity(self):
        """
        Getter for velocity
        """
        return self.vel

    @velocity.setter
    def velocity(self, vel : vec3, use_actual_value = False):
        """
        Setter for velocity
        - Takes the length of an arrow and sets the velocity proportional to it.
        """
        if use_actual_value:
            self.vel.x = vel.x
            self.vel.y = vel.y
            self.vel.z = 0
        else:
            self.vel.x = vel.x * ARROW_TO_VEL_RATIO
            self.vel.y = vel.y * ARROW_TO_VEL_RATIO
            self.vel.z = 0

    @property
    def position(self):
        return self.pos

    @position.setter
    def position(self, pos):
        if isinstance(pos, tuple):
            self.pos = vec3(pos[0], pos[1], 0)
            self.rect.center = pos
        elif isinstance(pos, vec3):
            self.pos = pos
            self.rect.center = (pos.x, pos.y)

    def update(self, dt):
        # Euler function - Updates self.pos, self.acc, and self.vel
        self.__integration_euler()


        # rotatin self.pos vec3 around in 3d

        p = self.pos
        x = vec3(1, 0, 0)
        y = vec3(0, 1, 0)
        z = vec3(0, 0, 1)
        xrot = glm.radians(self.world_rotation.x)
        yrot = glm.radians(self.world_rotation.y)
        zrot = glm.radians(self.world_rotation.z)
        p = vec4(p.x, p.y, p.z, 0)
        # p = p*scale
        M = glm.rotate(mat4(1), xrot, x)
        M = glm.rotate(M, yrot, y)
        M = glm.rotate(M, zrot, z)
        p = M*p
        p = vec3(p.x, p.y, p.z)
        print(f"Cam pos: {self.world_offset}, Cam rot: {self.world_rotation} Current vector center point of body: {p}")

        center_in_world = (p.x, p.y)
        self.rect.center = center_in_world   

        # # Update rect position from actual position
        # self.rect.center = (int(self.pos.x), int(self.pos.y))

        # # # Update image + rect (but not radius?) for zoom
        # # zoom_factor = 1
        # # if self.world_offset.z == 0:
        # #     self.image = self.__zero_image.convert_alpha()
        # #     self.rect = self.image.get_rect(center = (self.rect.center))
        # # else:
        # #     # Calc new drawing diameter
        # #     zoom_factor = (self.world_offset.z+100)/100
        # #     draw_diam = int(self.__radius*2*zoom_factor)
            
        # #     # Check if we need to scale
        # #     if draw_diam != self.rect.width:
        # #         # Check if we even need to show the body anymore
        # #         if draw_diam > 0:
        # #             new_size = [draw_diam]*2
        # #             print(f"Zoom factor: {zoom_factor} Drawing to new size {new_size} from {self.rect.width},{self.rect.height}")
        # #             self.image = pygame.transform.scale(self.__zero_image, new_size)
        # #         else:
        # #             surf = pygame.Surface((1,1)).convert_alpha()
        # #             surf.fill(PLANET_COLOR)
        # #             self.image = surf

        # #         self.rect = self.image.get_rect(center = (self.rect.center))

        # # # Update rect position based on world offset
        # # wx = zoom_factor*(self.rect.center[0] + int(self.world_offset.x))
        # # wy = zoom_factor*(self.rect.center[1] + int(self.world_offset.y))
        # # center_in_world = (wx, wy)
        # # self.rect.center = center_in_world

        # # Update rect position based on world offset
        # wx = self.rect.center[0]) + int(self.world_offset.x)
        # wy = self.rect.center[1]) + int(self.world_offset.y)
        # center_in_world = (wx, wy)
        # self.rect.center = center_in_world       

        self.rect.x += int(self.world_offset.x)
        self.rect.y += int(self.world_offset.y)

    def _correct_radius(self, radius):
        """
        Function to control the size of a celestial body.
        (Should be overridden by subclass)
        """
        if radius < 1:
            radius = 1
        return radius

    def __integration_euler(self):
        '''
        Calculates the new position and velocity using Euler integration method.
        
        The force is also added to the other object so it doesn't have to be 
        calculated twice.
        '''
        for obj in self.neighbours:
            if obj != self:
                f = self.__get_force(obj)
                self.F.x += f.x
                self.F.y += f.y
                if not self.force_just_calcd:                
                    obj.F.x -= f.x
                    obj.F.y -= f.y
                    obj.force_just_calcd = True
        self.force_just_calcd = True
            
        self.acc.x = self.F.x / self.mass
        self.acc.y = self.F.y / self.mass
        
        self.pos.x += self.vel.x * DELTA_T + 0.5 * self.acc.x * DELTA_T
        self.pos.y += self.vel.y * DELTA_T + 0.5 * self.acc.y * DELTA_T
        
        self.vel.x += self.acc.x * DELTA_T
        self.vel.y += self.acc.y * DELTA_T
        
        self.F = vec3(0) #resets force for the next iteration
        
    def __get_force(self, obj) -> vec3:
        '''
        Return the force between self and obj.
        '''
        vect = vec3(obj.pos.x - self.pos.x, obj.pos.y - self.pos.y, 0)
        dist = glm.distance(self.pos, obj.pos)
        factor = self.mass * obj.mass / dist**3 #Power of 3 because the directional vector is not normalized
        return vec3(vect.x*factor, vect.y*factor, 0)

class PlanetEntity(CelestialEntity):
    def __init__(self, center, **kwargs):
        super().__init__(center, **kwargs)   
 
        self.density = PLANET_DEFAULT_DENSITY

        size = 2*self.radius+2
        surf = pygame.Surface([size]*2, pygame.SRCALPHA)
        pygame.draw.circle(surf, PLANET_COLOR, [self.radius]*2, self.radius)
        self.image = surf.convert_alpha()
        self.rect = self.image.get_rect(center=center)

        # Store the original image copy to prevent scale transform artifacts
        self.__zero_image = self.image.convert_alpha()


    ###
    ### Public functions
    ###

    def update(self, dt):
        """
        Update function
        """
        super().update(dt) 
 

    ###
    ### Private functions 
    ###

    def _correct_radius(self, radius):
        """
        Private function to limit radius min and max
        (used by __init__ and in radius @setter)
        """
        if radius > PLANET_MAX_RADIUS:
            return PLANET_MAX_RADIUS
        elif radius < PLANET_MIN_RADIUS:
            return PLANET_MIN_RADIUS

        return radius
    