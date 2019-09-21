import time

import pygame

chooser_tabs = [
    {
        'label': 'Alphas',
        'keys': [
            ['KC_A', 'KC_B', 'KC_C', 'KC_D', 'KC_E', 'KC_F', 'KC_G', 'KC_H', 'KC_I', 'KC_J', 'KC_K', 'KC_L', 'KC_M'],
            ['KC_N', 'KC_O', 'KC_P', 'KC_Q', 'KC_R', 'KC_S', 'KC_T', 'KC_U', 'KC_V', 'KC_W', 'KC_X', 'KC_Y', 'KC_Z'],
            ['KC_1', 'KC_2', 'KC_3', 'KC_4', 'KC_5', 'KC_6', 'KC_7', 'KC_8', 'KC_9', 'KC_0', None, None, None],
        ]
    },
    {
        'label': 'Mods',
        'keys': [
            ['KC_ESC', 'KC_GESC', 'KC_GRAVE', None, 'KC_DEL', 'KC_INS', 'KC_BSPC', None, None, None, None, None, None],
            ['KC_N', 'KC_O', 'KC_P', 'KC_Q', 'KC_R', 'KC_S', 'KC_T', 'KC_U', 'KC_V', 'KC_W', 'KC_X', 'KC_Y', 'KC_Z'],
            ['KC_1', 'KC_2', 'KC_3', 'KC_4', 'KC_5', 'KC_6', 'KC_7', 'KC_8', 'KC_9', 'KC_0', 'KC_X', 'KC_Y', 'KC_Z'],
        ]
    }
]


class ProgramDisplay(object):
    def __init__(self, keymap, width=1024, height=768):
        self.keymap = keymap

        pygame.mixer.pre_init(44100, -16, 1, 1024)
        pygame.init()

        self.screen = pygame.display.set_mode((width, height))
        self.selected_layer = 0
        self.selected_chooser = 0

        self._set_dims()

        self.text_cache = {}
        self.get_font()

        self.in_progress = False

        self.kb_dirty = True
        self.chooser_dirty = True
        self.layer_dirty = True

    def _set_dims(self):
        screen_w, screen_h = self.screen.get_size()

        # 1/2 unit side padding
        self.x_unit = screen_w // (max(self.keymap.max_x, 14) + 1)
        self.y_unit = screen_h // self.keymap.max_y + 5

        if self.y_unit > self.x_unit:
            self.y_unit = self.x_unit

        self.screen_w = screen_w
        self.screen_h = screen_h

        kb_w = self.keymap.max_x * self.x_unit
        kb_h = self.keymap.max_y * self.y_unit

        kb_x = (screen_w - kb_w) // 2
        kb_y = self.y_unit

        self.kb_r = pygame.Rect(kb_x, kb_y, kb_w, kb_h)
        self.kb_surface = self.screen.subsurface(self.kb_r)

        # layer surface
        self.layer_r = pygame.Rect(0, self.y_unit * 0.25,
                                   screen_w, self.y_unit // 2)
        self.layer_surface = self.screen.subsurface(self.layer_r)

        # progress surface
        progress_r = pygame.Rect(0, 0, screen_w, self.y_unit * 0.2)
        self.progress_surface = self.screen.subsurface(progress_r)

        # chooser surface
        self.chooser_r = pygame.Rect(0, self.y_unit * (self.keymap.max_y + 1),
                                     screen_w, self.y_unit * 4)
        self.chooser_surface = self.screen.subsurface(self.chooser_r)

    def start_progress(self):
        self.progress = 0
        self.in_progress = True

        self.progress_update()
        pygame.display.update()

    def end_progress(self):
        self.in_progress = False

        self.progress_update()
        pygame.display.update()

    def update_progress(self, percent):
        self.in_progress = True
        self.progress = min(percent, 1.0)

        self.progress_update()
        pygame.display.update()

        if self.progress == 1.0:
            self.in_progress = False
            time.sleep(0.1)
            self.progress_update()
            pygame.display.update()

    def get_font(self):
        available = pygame.font.get_fonts()

        # prefer bottom up
        goodfonts = ['bitstreamverasansmono',
                     'liberationmono',
                     'freemono',
                     'monaco',
                     'consolas',
                     'pragmatapro',
                     'pragmatapromono']

        which = goodfonts[0]

        for item in goodfonts:
            if item in available:
                which = item

        self.key_font = pygame.font.SysFont(which, 14)

    def get_text(self, what, font, color):
        what = ''.join(i for i in what if ord(i) < 128)

        key = '-'.join(map(str, [what, font, color]))
        if key not in self.text_cache:
            image = font.render(what, True, color)
            self.text_cache[key] = image
        return self.text_cache[key]

    def get_label_text(self, what, color=pygame.Color('white')):
        return self.get_text(what, self.key_font, color)

    def progress_update(self):
        screen = self.progress_surface
        screen_w, screen_h = screen.get_size()

        screen.fill(pygame.Color('Black'))
        if not self.in_progress:
            return

        width = self.progress * screen_w

        bar_rect = pygame.Rect(0, 0, width, screen_h)
        pygame.draw.rect(screen, pygame.Color('white'), bar_rect, 0)

    def chooser_update(self):
        if not self.chooser_dirty:
            return False

        self.chooser_dirty = False

        screen = self.chooser_surface
        screen_w, screen_h = screen.get_size()

        tab_screen = screen.subsurface(pygame.Rect(
            0, 0.25 * self.y_unit,
            screen_w, 0.5 * self.y_unit))

        tab_width = screen_w // len(chooser_tabs)
        tab_height = 0.5 * self.y_unit

        tab_screen.fill(pygame.Color('Black'))

        for idx, tab in enumerate(chooser_tabs):
            if idx == self.selected_chooser:
                border_width = 0
                font_color = pygame.Color('black')
            else:
                border_width = 1
                font_color = pygame.Color('white')

            l_rect = pygame.Rect(
                tab_width * idx, 0,
                tab_width, tab_height)

            pygame.draw.rect(tab_screen, pygame.Color('white'),
                             l_rect, border_width)

            label = self.get_label_text(tab['label'], color=font_color)
            xpos = l_rect.x + (l_rect.w // 2) - (label.get_width() // 2)
            ypos = l_rect.y + (l_rect.h // 2) - (label.get_height() // 2)
            tab_screen.blit(label, (xpos, ypos))

        key_width = 13 * self.x_unit
        key_ofs = (screen_w - key_width) // 2

        key_rect = pygame.Rect(
            key_ofs, self.y_unit,
            key_width, self.y_unit * 3)

        key_screen = screen.subsurface(key_rect)

        keys = chooser_tabs[self.selected_chooser]['keys']
        for row in range(len(keys)):
            for col in range(len(keys[row])):
                keyrect = pygame.Rect(
                    (self.x_unit * col) + 1, (self.y_unit * row) + 1,
                    self.x_unit - 2, self.y_unit - 2)

                pygame.draw.rect(key_screen,
                                 pygame.Color('gray29'), keyrect, 0)
                pygame.draw.rect(key_screen,
                                 pygame.Color('white'), keyrect, 1)

                label_txt = keys[row][col]

                if label_txt:
                    label = self.get_label_text(label_txt)
                    xpos = keyrect.x + (keyrect.w // 2) - (label.get_width() // 2)
                    ypos = keyrect.y + (keyrect.h // 2) - (label.get_height() // 2)
                    key_screen.blit(label, (xpos, ypos))

        return True

    def layer_update(self):
        if not self.layer_dirty:
            return False

        self.layer_dirty = False

        screen = self.layer_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // self.keymap.layers

        screen.fill(pygame.Color('Black'))

        for layer in range(self.keymap.layers):
            if layer == self.selected_layer:
                border_width = 0
                font_color = pygame.Color('black')
            else:
                border_width = 1
                font_color = pygame.Color('white')

            l_rect = pygame.Rect(
                button_width * layer, 0,
                button_width, screen_h)

            pygame.draw.rect(screen, pygame.Color('white'),
                             l_rect, border_width)

            label = self.get_label_text('Layer %d' % layer, color=font_color)
            xpos = l_rect.x + (l_rect.w // 2) - (label.get_width() // 2)
            ypos = l_rect.y + (l_rect.h // 2) - (label.get_height() // 2)
            screen.blit(label, (xpos, ypos))

        return True

    def on_layer_mousedown(self, pos):
        screen = self.layer_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // self.keymap.layers

        which_layer = int(pos[0] // button_width)

        self.selected_layer = which_layer
        self.layer_dirty = True
        self.kb_dirty = True

    def kb_update(self):
        if not self.kb_dirty:
            return False

        self.kb_dirty = False

        x_unit = self.x_unit
        y_unit = self.y_unit
        screen = self.kb_surface

        screen.fill(pygame.Color('Black'))

        for item in self.keymap.keylist:
            keyrect = pygame.Rect(x_unit * item['x'] + 1, y_unit * item['y'] + 1,
                                  x_unit * item['w'] - 2, y_unit * item['h'] - 2)

            pygame.draw.rect(screen, pygame.Color('gray29'), keyrect, 0)
            pygame.draw.rect(screen, pygame.Color('white'), keyrect, 1)

            label_txt = self.keymap.label_for_key(self.selected_layer, item)

            if label_txt:
                label = self.get_label_text(label_txt)
                xpos = keyrect.x + (keyrect.w // 2) - (label.get_width() // 2)
                ypos = keyrect.y + (keyrect.h // 2) - (label.get_height() // 2)
                screen.blit(label, (xpos, ypos))
        return True

    def run(self):
        self.screen.fill(pygame.Color('black'))

        self.kb_update()
        pygame.display.update()

        pygame.display.set_caption(
            'Loading Keymap for "%s"' % self.keymap.name)

        self.start_progress()
        self.keymap.get_map(self.update_progress)
        self.end_progress()
        self.kb_dirty = True

        pygame.display.set_caption('Programming "%s"' % self.keymap.name)

        done = False
        while not done:
            event = pygame.event.poll()
            while event:
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.layer_r.collidepoint(event.pos):
                            self.on_layer_mousedown(event.pos)

                event = pygame.event.poll()

            if self.layer_update() or \
               self.kb_update() or \
               self.chooser_update():
                pygame.display.update()

            time.sleep(0.1)

        pygame.quit()
