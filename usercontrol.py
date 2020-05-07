import pygame as pg

class UserControlGroup:
    def __init__(self):
        self._members = pg.sprite.Group()
        self._bounds = pg.Rect(0,0,0,0)

    def process_events(self, events):
        for e in events:
            if e.type == pg.MOUSEBUTTONDOWN:
                self.mouse_down(pg.mouse.get_pos())
            if e.type == pg.MOUSEBUTTONUP:
                self.mouse_up(pg.mouse.get_pos())
            if e.type == pg.KEYDOWN:
                self.key_down(e)
            if e.type == pg.KEYUP:
                self.key_up(e)

    def update(self, *args):
        for m in self._members:
            m.update(*args)

    def draw(self, surface):
        for m in self._members:
            surface.blit(m.image, (m.rect.x, m.rect.y))

    def get_input(self, name):
        for m in self._members:
            if m.name == name:
                return m

        print(f"No input named '{name}' exists")
        return None

    def mouse_down(self, mouse_pos):
        any_hit = 0
        for m in self._members:
            hit = m.rect.collidepoint(mouse_pos)
            if hit:
                m.on_mousedown()
                self.set_focus_on(m)
                any_hit = 1
                break

        if not any_hit:
            for m in self._members:
                m.reset()
                self.set_focus_on(None)

    def mouse_up(self, mouse_pos):
        any_hit = 0
        for m in self._members:
            hit = m.rect.collidepoint(mouse_pos)
            if hit:
                m.on_mouseup()
                any_hit = 1
                break

        if not any_hit:
            for m in self._members:
                m.reset()

    def key_down(self, key_event):
        for m in self._members:
            if m.has_focus:
                m.on_keydown(key_event)
                break

    def key_up(self, key_event):
        pass

    def set_focus_on(self, ip):
        for m in self._members:
            if m is ip:
                m.has_focus = True
            else:
                m.has_focus = False

    #def remove_focus_except(self, ip):
    #    for m in self._members:
    #        if not m is ip:
    #            m.has_focus = False

    def clear(self):
        self._members = []

    def __bool__(self):
        return bool(self._members)

    def __len__(self):
        return len(self._members)

    def __iadd__(self, ip):
        self.add(ip)
        return self

    def __isub__(self, ip):
        for i, m in enumerate(self._members):
            if m is ip:
                del self._members[i]
                return self
        return self

    def add(self, ip):
        assert ip is not None
        for m in self._members:
            if ip.name == m.name:
                raise ValueError(f"Already have an input named: {ip.name}")

        self._members.add(ip)
        return self

    def __iter__(self):
        return iter(self._members)

    def _calculate_bounds(self):
        minx = 0
        miny = 0
        maxx = 0
        maxy = 0
        for m in self._members:
            if m.rect.x < minx:
                minx = m.rect.x
            if m.rect.y < miny:
                miny = m.rect.y
            if m.rect.x+m.rect.width > maxx:
                maxx = m.rect.x+m.rect.width
            if m.rect.y+m.rect.height > maxy:
                maxy = m.rect.y+m.rect.height
        self._bounds.x = minx
        self._bounds.y = miny
        self._bounds.width = maxx-minx
        self._bounds.height = maxy-miny

class UserControl(pg.sprite.Sprite):
    def __init__(self, parent_group, name, **kwargs):
        super().__init__()

        self._down = False
        self._has_focus = False

        self._name = name
        self._center = kwargs.pop("center", (0,0))
        self._text = kwargs.pop("text", '')
        self._font = kwargs.pop("font", pg.font.SysFont('Arial', 16, False, False))
        min_size = self._font.size(self._text)
        self._width = kwargs.pop("width", min_size[0])
        self._height = kwargs.pop("height", min_size[1]*2)
        self._padding = kwargs.pop("padding", 20)
        self._bg_color = kwargs.pop("bg_color", (0,0,0))
        self._fg_color = kwargs.pop("fg_color", (255,255,255))
        self._hl_color = kwargs.pop("hl_color", (0,100,200))
        self._border_thick = kwargs.pop("border_thick", 2)
        self._text_align = kwargs.pop("text_align", 1) # 1: left, 2: center, 3: right
        self._on_click_fn = kwargs.pop("on_click", lambda: None)
        self._bg_image = kwargs.pop("image", None)

        if self._bg_image:
            self.image = self._bg_image
        else:
            surf = pg.Surface((self._width, self._height))
            self.image = surf.convert()

        self.rect = self.image.get_rect(center = self._center)

        self._render_chain = [
                self._render_bg,
                self._render_text,
                self._render_border
            ]
        self._image_background = False

        self._dirty = True

        self._dt = 0

        self.parent_group = parent_group
        parent_group += self

        self._layer = 100

    @property
    def bg_image(self):
        if self._image_background:
            return self.image
        else:
            return None

    @bg_image.setter
    def bg_image(self, image):
        self._image_background = True
        self.image = image
        self.rect = self.image.get_rect()
        self._dirty = True

    def update(self, *args):
        self._render_internal()

    def _render_internal(self):
        # if self._image_background: return
        if not self._dirty: return

        foreground = pg.Color(self._fg_color[0], self._fg_color[1], self._fg_color[2])
        background = pg.Color(self._bg_color[0], self._bg_color[1], self._bg_color[2])
        highlight = pg.Color(self._hl_color[0], self._hl_color[1], self._hl_color[2])

        surf = pg.Surface([self.rect.width, self.rect.height])
        for r in self._render_chain:
            r(surf, self._width, self._height, foreground, background, highlight, self._padding, self._font, self._text, self._border_thick)

        self.image = surf.convert()
        self._dirty = False

    def _render_bg(self, surf, width, height, foreground, background, highlight, padding, font, text, border_thick):
        if self._image_background:
            surf.blit(self._bg_image, (0, 0))
        else:
            surf.fill(background)

    def _render_text(self, surf, width, height, foreground, background, highlight, padding, font, text, border_thick):
        tcol = highlight if self._has_focus else foreground
        tsurf = self._font.render(self._text, True, tcol)
        tsize = self._font.size(self._text)
        tpos = [0,0]
        tadj = [0,0] if tsize[0] <= self._width-self._padding*2 else [self._width-self._padding*2-tsize[0], 0]

        if self._text_align == 1:
            tpos = [self._padding+tadj[0], self._height//2 - tsize[1]//2]
        elif self._text_align == 2:
            tpos = [self._width//2-tsize[0]//2+tadj[0], self._height//2 - tsize[1]//2]
        elif self._text_align == 3:
            tpos = [self._width-tsize[0]-self._padding+tadj[0], self._height//2 - tsize[1]//2]
        surf.blit(tsurf, tpos)

    def _render_border(self, surf, width, height, foreground, background, highlight, padding, font, text, border_thick):
        if self._has_focus:
            pg.draw.rect(surf, highlight, pg.Rect(0,0,self._width-1, self._height-1), 4)
        elif self._border_thick > 0:
            pg.draw.rect(surf, foreground, pg.Rect(0,0,self._width-self._border_thick//2, self._height-self._border_thick//2), self._border_thick)

    def reset(self):
        self._down = False

    @property
    def has_focus(self):
        return self._has_focus

    @has_focus.setter
    def has_focus(self, b):
        self._has_focus = b
        self._dirty = True

    @property
    def name(self):
        return self._name

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, x):
        self.rect.x = x

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, y):
        self.rect.y = y

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, wid):
        self._width = wid
        ow = self.rect.width
        self.rect.width = wid
        self.rect.x += ow-wid

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, hgt):
        self._height = hgt
        oh = self.rect.height
        self.rect.height = hgt
        self.rect.y += oh-hgt

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, txt):
        self._text = txt
        self._dirty = True

    def on_mousedown(self):
        if not self._down:
            self._down = True
        self._dirty = True

    def on_mouseup(self):
        if self._down:
            self._down = False
        self._dirty = True

    def on_keydown(self, key_event):
        self._dirty = True

    def on_keyup(self, key_event):
        self._dirty = True

class Button(UserControl):
    def __init__(self, parent_group, name, **kwargs):
        ta = kwargs.pop("text_align", 2)
        fg = kwargs.pop("fg_color", (255,255,255))
        bg = kwargs.pop("bg_color", (0,0,0))
        bt = kwargs.pop("border_thick", 0)
        super().__init__(parent_group, name, text_align = ta, fg_color = fg, bg_color = bg, border_thick = bt, **kwargs)
    
    def on_mousedown(self):
        super().on_mousedown()

    def on_mouseup(self):
        super().on_mouseup()
        self._on_click_fn()
        self._has_focus = False

    @staticmethod
    def from_image(image, parent_group, name, **kwargs):
        b = Button(parent_group, name, **kwargs)
        b.image = image
        return b

class ToggleButton(UserControl):
    def __init__(self, parent_group, name, **kwargs):
        ta = kwargs.pop("text_align", 2)
        fg = kwargs.pop("fg_color", (255,255,255))
        bg = kwargs.pop("bg_color", (0,0,0))
        bt = kwargs.pop("border_thick", 0)
        super().__init__(parent_group, name, text_align = ta, fg_color = fg, bg_color = bg, border_thick = bt, **kwargs)
        
        self._image1 = kwargs.pop("image1", None)
        self._image2 = kwargs.pop("image2", None)

        self.toggle_state = True
        self._on_click_fn = lambda: self.__toggle_button()
        self._on_click_fn1 = kwargs.pop("function1", lambda: None)
        self._on_click_fn2 = kwargs.pop("function2", lambda: None)

    def __toggle_button(self):
        c = self._bg_color
        self._bg_color = self._fg_color
        self._fg_color = c
        self._dirty = True

    def on_mousedown(self):
        super().on_mousedown()

    def on_mouseup(self):
        super().on_mouseup()
        self._on_click_fn()
        self._has_focus = False

    @property
    def image1(self):
        if self._image_background:
            return self.image1
        else:
            return None

    @image1.setter
    def image1(self, image):
        self._image_background = True
        self._image1 = image
        self.image = image
        self.rect = self.image.get_rect()
        self._dirty = True

    @property
    def image2(self):
        if self._image_background:
            return self.image2
        else:
            return None

    @image2.setter
    def image2(self, image):
        self._image_background = True
        self._image2 = image
        # self.rect = self.image.get_rect()
        self._dirty = True

    @staticmethod
    def from_images(image1, image2, parent_group, name, **kwargs):
        tb = ToggleButton(parent_group, name, image1 = image1, image2 = image2, **kwargs)
        return tb

class TextBox(UserControl):
    def __init__(self, parent_group, name, **kwargs):
        ta = kwargs.pop("text_align", 1)
        fg = kwargs.pop("fg_color", (0,0,0))
        bg = kwargs.pop("bg_color", (255,255,255))
        super().__init__(parent_group, name, text_align = ta, fg_color = fg, bg_color = bg, **kwargs)

    def on_keydown(self, key_event):
        super().on_keydown(key_event)
        if key_event.key == pg.K_BACKSPACE:
            if self._text: self._text = self._text[:-1]
        else:
            chr = key_event.unicode
            if chr:
                self._text += chr

class Label(UserControl):
    def __init__(self, parent_group, name, **kwargs):
        ta = kwargs.pop("text_align", 1)
        fg = kwargs.pop("fg_color", (0,0,0))
        bg = kwargs.pop("bg_color", (255,255,255))
        bt = kwargs.pop("border_thick", 0)
        super().__init__(parent_group, name, text_align = ta, fg_color = fg, bg_color = bg, border_thick = bt, **kwargs)

class ChoiceBox(UserControl):
    def __init__(self, parent_group, name, items, **kwargs):
        ta = kwargs.pop("text_align", 1)
        fg = kwargs.pop("fg_color", (0,0,0))
        bg = kwargs.pop("bg_color", (255,255,255))
        super().__init__(parent_group, name, text_align = ta, fg_color = fg, bg_color = bg, **kwargs)

        self._items = []
        if isinstance(items, list): self._items = items
        else: raise ValueError("Items variable must be a list")

        self._item_idx = 0

        self._render_chain.insert(len(self._render_chain)-2, self._render_arrows)

    def _render_arrows(self, surf, width, height, foreground, background, highlight, padding, font, text, border_thick):
        aw = self._height//6
        wf = 1.2
        down_points = [[-aw*wf//2, -aw//2//wf], [aw*wf//2, -aw//2//wf], [0, aw//2//wf]]
        up_points = [[-aw*wf//2, aw//2//wf], [aw*wf//2, aw//2//wf], [0, -aw//2//wf]]
        m = height-aw*2
        for d in down_points:
            d[0] += width-border_thick*4-aw//2
            d[1] += height//2+aw//2+m//8
        for u in up_points:
            u[0] += width-border_thick*4-aw//2
            u[1] += height//2-aw//2-m//8

        clr = highlight if self._has_focus else foreground
        #Down arrow background and arrow
        pg.draw.rect(surf, background, pg.Rect(width-aw-m//4, height//2, aw+m//4, height//2), 0)
        pg.draw.polygon(surf, clr, down_points, 0)
        
        #Up arrow background and arrow
        pg.draw.rect(surf, background, pg.Rect(width-aw-m//4, 0, aw+m//4, height//2), 0)
        pg.draw.polygon(surf, clr, up_points, 0)

    def update(self, *args):
        if self._items:
            self._text = self._items[self._item_idx]
        else:
            self._text = "No Items"
        super().update(*args)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        if isinstance(items, list):
            self._items.clear()
            for i in items:
                if isinstance(i, str): self._items.append(i)
                else:
                    try:
                        self._items.append(str(i))
                    except:
                        print("Could not add item: {i}")
            self._dirty = True
        elif isinstance(items, str):
            self._items.append(str)
            self._dirty = True
        else:
            print("Unsupported item added to choicebox")

    def on_keydown(self, key_event):
        super().on_keydown(key_event)
        if key_event.key == pg.K_UP:
            self._item_idx -= 1
            if self._item_idx < 0: self._item_idx = len(self._items)-1
            self._dirty = True
        elif key_event.key == pg.K_DOWN:
            self._item_idx += 1
            if self._item_idx > len(self._items)-1: self._item_idx = 0
            self._dirty = True
