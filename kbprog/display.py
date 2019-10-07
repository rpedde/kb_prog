import logging
import time

import pygame

from kbprog import keys


chooser_tabs = [
    {
        'label': '60%',
        'keys': [
            ['KC_ESC', 'KC_1', 'KC_2', 'KC_3', 'KC_4', 'KC_5', 'KC_6', 'KC_7', 'KC_8', 'KC_9', 'KC_0', 'KC_MINS', 'KC_EQL', 'KC_BSPC'],
            ['KC_TAB', 'KC_Q', 'KC_W', 'KC_E', 'KC_R', 'KC_T', 'KC_Y', 'KC_U', 'KC_I', 'KC_O', 'KC_P', 'KC_LBRC', 'KC_RBRC', 'KC_BSLS'],
            ['KC_CAPS', 'KC_A', 'KC_S', 'KC_D', 'KC_F', 'KC_G', 'KC_H', 'KC_J', 'KC_K', 'KC_L', 'KC_SCLN', 'KC_QUOT', 'KC_ENT', None],
            ['KC_LSFT', 'KC_Z', 'KC_X', 'KC_C', 'KC_V', 'KC_B', 'KC_N', 'KC_M', 'KC_COMM', 'KC_DOT', 'KC_SLSH', 'KC_RSFT', None, None],
            ['KC_LCTL', 'KC_LGUI', 'KC_LALT', None, None, 'KC_SPC', None, None, 'KC_RALT', 'KC_RGUI', 'KC_MENU', 'KC_RCTL', None, None],
        ]
    },
    {
        'label': 'FN/TKL',
        'keys': [
            ['KC_F1', 'KC_F2', 'KC_F3', 'KC_F4', 'KC_F5', 'KC_F6', 'KC_F7', 'KC_F8', 'KC_F9', 'KC_F10', 'KC_F11', 'KC_F12', None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None ],
            [None, None, 'KC_UP', None, None, None, None, None, None, None, None, 'KC_PSCR', 'KC_SLCK', 'KC_PAUS'],
            [None, 'KC_LEFT', 'KC_DOWN', 'KC_RGHT', None, None, None, None, None, None, None, 'KC_INS', 'KC_HOME', 'KC_PGUP'],
            [None, None, None, None, None, None, None, None, None, None, None, 'KC_DEL', 'KC_END', 'KC_PGDN'],
        ]
    },
    {
        'label': 'Numpad/Macro',
        'keys': [
            ['KC_NLCK', 'KC_PSLS', 'KC_PAST', 'KC_PMNS', None, 'MACRO00', 'MACRO01', 'MACRO02', 'MACRO03', 'MACRO04', 'MACRO05', 'MACRO06', 'MACRO07', None ],
            ['KC_P7', 'KC_P8', 'KC_P9', 'KC_PPLS', None, 'MACRO08', 'MACRO09', 'MACRO10', 'MACRO11', 'MACRO12', 'MACRO13', 'MACRO14', 'MACRO15', None ],
            ['KC_P4', 'KC_P5', 'KC_P6', None, None, None, None, None, None, None, None, None, None ],
            ['KC_P1', 'KC_P2', 'KC_P3', 'KC_PENT', None, None, None, None, None, None, None, None, None, None ],
            ['KC_P0', 'KC_PDOT', 'KC_PCMM', None, None, None, None, None, None, None, None, None, None, None ],
        ]
    },
    {
        'label': 'Special',
        'keys': [
            [None, 'MO(1)', 'MO(2)', 'MO(3)', None, 'FN_MO13', 'FN_MO23', None, None, 'KC_GRV', 'KC_GESC', None, None, 'KC_TRNS', 'KC_NO'],
            ['DF(0)', 'DF(1)', 'DF(2)', 'DF(3)', None, None, None, None, None, None, None, None, 'DEBUG', 'RESET' ],
            [None, None, None, None, None, None, None, None,                             None, 'MW_UP', None, None, 'MS_UP', None ],
            ['BR_INC', 'EF_INC', 'ES_INC', 'H1_INC', 'S1_INC', 'H2_INC', 'S2_INC', None, 'MW_LEFT', 'MW_DOWN', 'MW_RIGHT', 'MS_LEFT', 'MS_DOWN', 'MS_RIGHT' ],
            ['BR_DEC', 'EF_DEC', 'ES_DEC', 'H1_DEC', 'S1_DEC', 'H2_DEC', 'S2_DEC', None, None, 'MS_BTN1', 'MS_BTN2', 'MS_BTN3', 'MS_BTN4', 'MS_BTN5'],
        ]
    },
    {
        'label': 'Media/BL',
        'keys': [
            ['KC_MPRV', 'KC_MSTP', 'KC_MNXT', None, 'KC_MUTE', 'KC_VOLU', 'KC_VOLD', None, 'BL_OFF', 'BL_ON', 'BL_TOGG', None, None, None ],
            ['KC_MRWD', 'KC_MPLY', 'KC_MFFD', None, None, None, None, None, 'BL_DEC', 'BL_INC', 'BL_STEP', 'BL_BRTG', None, None ],
            [None, 'KC_MSEL', 'KC_EJCT', None, 'RGB_TOG', 'RGB_MOD', 'RGB_RMOD', None, None, None, None, None, None, None ],
            [None, None, None, None, 'RGB_HUI', 'RGB_HUD', 'RGB_SAI', 'RGB_SAD', 'RGB_VAI', 'RGB_VAD', 'RGB_SPI', 'RGB_SPD', None, None ],
            [None, None, None, None, 'RGB_M_P', 'RGB_M_B', 'RGB_M_R', 'RGB_M_SW', 'RGB_M_SN', 'RGB_M_K', 'RGB_M_X', 'RGB_M_G', None, None ],
        ]
    }
]

for item in chooser_tabs:
    rowlist = item['keys']
    for row in rowlist:
        for keyitem in row:
            if keyitem not in keys.key_to_bytes and keyitem is not None:
                raise RuntimeError('Bad key: %s' % keyitem)


class ProgramDisplay(object):
    def __init__(self, keymap, width=1024, height=768):
        self.keymap = keymap

        pygame.mixer.pre_init(44100, -16, 1, 1024)
        pygame.init()

        self.screen = pygame.display.set_mode((width, height))
        self.selected_layer = 0
        self.selected_chooser = 0
        self.selected_keymap = 0
        self.hover_keymap = 0

        self._set_dims()

        self.text_cache = {}
        self.get_font()

        self.in_progress = False

        self.kb_hover = None
        self.kb_dirty = True
        self.chooser_dirty = True
        self.layer_dirty = True
        self.program_dirty = False
        self.action_dirty = True

        self.logger = logging.getLogger(__name__)

        self.action_tabs = [
            {'label': 'program',
             'type': 'action',
             'enabled': False,
             'action': self.program},
            {'label': 'labels',
             'type': 'value',
             'value': True}
        ]

    def _set_dims(self):
        screen_w, screen_h = self.screen.get_size()

        self.chooser_key_cols = 14
        self.chooser_key_rows = 5

        # 1/2 unit side padding
        self.x_unit = screen_w // (max(
            self.keymap.max_x + 1,
            self.chooser_key_cols + 1))
        self.y_unit = screen_h // (    # three 1u menus, plus key rows
            self.keymap.max_y + self.chooser_key_rows + 3)

        self.y_unit = min(self.y_unit, self.x_unit)
        self.x_unit = self.y_unit

        # if self.y_unit > self.x_unit:
        #     self.y_unit = self.x_unit

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

        # chooser tab
        self.chooser_tab_r = pygame.Rect(
            0, self.chooser_r.y + (0.25 * self.y_unit),
            screen_w,
            0.5 * self.y_unit)

        self.chooser_tab_surface = self.screen.subsurface(self.chooser_tab_r)

        # chooser_keys
        key_width = self.chooser_key_cols * self.x_unit
        key_ofs = (screen_w - key_width) // 2

        self.chooser_key_r = pygame.Rect(
            key_ofs, self.y_unit + self.chooser_r.y,
            key_width, self.y_unit * self.chooser_key_rows)

        self.chooser_key_surface = self.screen.subsurface(self.chooser_key_r)

        # action tab
        self.action_tab_r = pygame.Rect(
            0, self.screen_h - (self.y_unit * 0.75),
            self.screen_w, self.y_unit * 0.5)

        self.action_tab_surface = self.screen.subsurface(self.action_tab_r)

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

    def program(self):
        pygame.display.set_caption('Programming "%s"' % self.keymap.name)

        self.keymap.program(self.update_progress)
        self.action_tabs[0]['enabled'] = False

        pygame.display.set_caption('Editing "%s"' % self.keymap.name)

        self.kb_dirty = True
        self.action_dirty = True

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

        self.logger.debug('starting chooser update')

        screen = self.chooser_surface
        screen_w, screen_h = screen.get_size()

        tab_width = screen_w // len(chooser_tabs)
        tab_height = 0.5 * self.y_unit

        tab_screen = self.chooser_tab_surface
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

        key_screen = self.chooser_key_surface
        key_screen.fill(pygame.Color('Black'))

        c_keys = chooser_tabs[self.selected_chooser]['keys']
        for row in range(len(c_keys)):
            for col in range(len(c_keys[row])):
                keyrect = pygame.Rect(
                    (self.x_unit * col) + 1, (self.y_unit * row) + 1,
                    self.x_unit - 2, self.y_unit - 2)

                key_color = pygame.Color('gray29')

                label_txt = c_keys[row][col]
                font_color = pygame.Color('white')
                if label_txt is not None:
                    if label_txt == self.hover_keymap:
                        key_color = pygame.Color('green')
                        font_color = pygame.Color('black')
                    if label_txt == self.selected_keymap:
                        key_color = pygame.Color('red')
                        font_color = pygame.Color('black')

                    pygame.draw.rect(key_screen, key_color, keyrect, 0)
                    pygame.draw.rect(key_screen,
                                     pygame.Color('white'), keyrect, 1)

                    if self.action_tabs[1]['value']:
                        labs = list(keys.key_to_labels[label_txt])
                        if all(x == '' for x in labs):
                            labs[1] = label_txt

                        for idx, label_txt in enumerate(labs):
                            if label_txt != '':
                                label = self.get_label_text(label_txt, color=font_color)
                                xpos = keyrect.x + 4
                                yofs = label.get_height() // 2
                                ypos = keyrect.y + (idx * (self.y_unit // 4)) + yofs
                                key_screen.blit(label, (xpos, ypos))
                    else:
                        label = self.get_label_text(label_txt, color=font_color)
                        xpos = keyrect.x + (keyrect.w // 2) - (label.get_width() // 2)
                        ypos = keyrect.y + (keyrect.h // 2) - (label.get_height() // 2)
                        key_screen.blit(label, (xpos, ypos))

        self.logger.debug('chooser update complete')
        return True

    def action_update(self):
        if not self.action_dirty:
            return False

        self.logger.debug('starting action update')
        self.action_dirty = False

        screen = self.action_tab_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // len(self.action_tabs)

        screen.fill(pygame.Color('Black'))

        for idx, button in enumerate(self.action_tabs):
            bgcolor = pygame.Color('black')
            fgcolor = pygame.Color('white')

            if button.get('type', 'value') == 'value':
                # controlled by bool in "value"
                if button.get('value'):
                    bgcolor = pygame.Color('white')
                    fgcolor = pygame.Color('black')
            elif button.get('enabled', True) is False:
                fgcolor = pygame.Color('gray29')

            b_rect = pygame.Rect(
                button_width * idx, 0,
                button_width, screen_h)

            pygame.draw.rect(screen, bgcolor, b_rect, 0)
            pygame.draw.rect(screen, fgcolor, b_rect, 1)

            label = self.get_label_text(
                button.get('label', '?'), color=fgcolor)

            xpos = b_rect.x + (b_rect.w // 2) - (label.get_width() // 2)
            ypos = b_rect.y + (b_rect.h // 2) - (label.get_height() // 2)
            screen.blit(label, (xpos, ypos))

        self.logger.debug('action update complete')
        return True

    def layer_update(self):
        if not self.layer_dirty:
            return False

        self.layer_dirty = False

        self.logger.debug('starting layer update')

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

        self.logger.debug('layer update complete')
        return True

    def on_kb_move(self, pos):
        new_pos = (pos[0] - self.kb_r.x,
                   pos[1] - self.kb_r.y)
        self.kb_hover = new_pos
        self.kb_dirty = True

    def on_drop_key(self, pos):
        corrected_pos = (pos[0] - self.kb_r.x,
                         pos[1] - self.kb_r.y)

        if self.selected_keymap != 0:
            for item in self.keymap.keylist:
                if item['keyrect'].collidepoint(corrected_pos):
                    self.keymap.set_key(
                        self.selected_layer, item, self.selected_keymap)
                    self.action_tabs[0]['enabled'] = True

        self.selected_keymap = 0
        self.hover_keymap = 0
        self.kb_hover = None

        self.chooser_dirty = True
        self.kb_dirty = True
        self.action_dirty = True

    def on_chooser_key_move(self, pos):
        col = (pos[0] - self.chooser_key_r.x) // self.x_unit
        row = (pos[1] - self.chooser_key_r.y) // self.y_unit

        keys = chooser_tabs[self.selected_chooser]['keys']

        if keys[row][col] is not None:
            hover_keymap = keys[row][col]
            if hover_keymap == self.selected_keymap:
                self.hover_keymap = 0
            else:
                self.hover_keymap = hover_keymap
        else:
            self.hover_keymap = 0

        self.chooser_dirty = True

    def on_action_tab_mousedown(self, pos):
        screen = self.action_tab_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // len(self.action_tabs)

        which_button = int(pos[0] // button_width)

        b_info = self.action_tabs[which_button]

        b_type = b_info.get('type', 'value')

        if b_type == 'value':
            b_info['value'] = not b_info['value']
            self.action_dirty = True
            self.kb_dirty = True
            self.chooser_dirty = True
        elif b_type == 'action' and b_info.get('enabled', True):
            b_info['action']()

    def on_chooser_tab_mousedown(self, pos):
        screen = self.chooser_tab_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // len(chooser_tabs)

        which_button = int(pos[0] // button_width)

        self.logger.debug('chooser invalidated')
        self.selected_chooser = which_button
        self.chooser_dirty = True

    def on_layer_mousedown(self, pos):
        screen = self.layer_surface
        screen_w, screen_h = screen.get_size()

        button_width = screen_w // self.keymap.layers

        which_layer = int(pos[0] // button_width)

        self.logger.debug('layer invalidated')
        self.selected_layer = which_layer
        self.layer_dirty = True
        self.kb_dirty = True

    def kb_update(self):
        if not self.kb_dirty:
            return False

        self.kb_dirty = False

        self.logger.debug('starting kb update')

        x_unit = self.x_unit
        y_unit = self.y_unit
        screen = self.kb_surface

        screen.fill(pygame.Color('Black'))

        for item in self.keymap.keylist:
            if item.get('keyrect') is None:
                keyrect = pygame.Rect(
                    x_unit * item['x'] + 1, y_unit * item['y'] + 1,
                    x_unit * item['w'] - 2, y_unit * item['h'] - 2)
                item['keyrect'] = keyrect

            keyrect = item['keyrect']

            key_color = pygame.Color('gray29')

            if self.kb_hover is not None:
                if keyrect.collidepoint(self.kb_hover):
                    key_color = pygame.Color('green')

            pygame.draw.rect(screen, key_color, keyrect, 0)

            if self.keymap.is_dirty(self.selected_layer, item):
                pygame.draw.rect(screen, pygame.Color('red'),
                                 pygame.Rect(keyrect.x + 2,
                                             keyrect.y + 2,
                                             keyrect.w - 4,
                                             keyrect.h - 4), 3)

            pygame.draw.rect(screen, pygame.Color('white'), keyrect, 1)

            label_txt = self.keymap.label_for_key(self.selected_layer, item)
            if self.action_tabs[1]['value']:
                labs = list(keys.key_to_labels.get(label_txt, ('', label_txt, '')))
                if all(x == '' for x in labs):
                    labs[1] = label_txt

                for idx, label_txt in enumerate(labs):
                    if label_txt != '':
                        label = self.get_label_text(label_txt)
                        xpos = keyrect.x + 4
                        yofs = label.get_height() // 2
                        ypos = keyrect.y + (idx * (self.y_unit // 4)) + yofs
                        screen.blit(label, (xpos, ypos))
            else:
                if label_txt:
                    label = self.get_label_text(label_txt)
                    xpos = keyrect.x + (keyrect.w // 2) - (label.get_width() // 2)
                    ypos = keyrect.y + (keyrect.h // 2) - (label.get_height() // 2)
                    screen.blit(label, (xpos, ypos))

        self.logger.debug('kb update complete')
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

        pygame.display.set_caption('Editing "%s"' % self.keymap.name)

        done = False
        while not done:
            event = pygame.event.poll()
            while event:
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                elif event.type == pygame.MOUSEMOTION:
                    if self.chooser_key_r.collidepoint(event.pos):
                        self.on_chooser_key_move(event.pos)
                    elif self.kb_r.collidepoint(event.pos):
                        if self.selected_keymap != 0:
                            self.on_kb_move(event.pos)
                    else:
                        if self.hover_keymap != 0:
                            self.hover_keymap = 0
                            self.chooser_dirty = True
                        if self.kb_hover is not None:
                            self.kb_hover = None
                            self.kb_dirty = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if self.kb_r.collidepoint(event.pos):
                            self.on_drop_key(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.layer_r.collidepoint(event.pos):
                            self.on_layer_mousedown(event.pos)
                        elif self.chooser_tab_r.collidepoint(event.pos):
                            self.on_chooser_tab_mousedown(event.pos)
                        elif self.chooser_key_r.collidepoint(event.pos):
                            self.selected_keymap = self.hover_keymap
                            self.chooser_dirty = True
                        elif self.action_tab_r.collidepoint(event.pos):
                            self.on_action_tab_mousedown(event.pos)

                event = pygame.event.poll()

            refresh = False
            refresh |= self.layer_update()
            refresh |= self.chooser_update()
            refresh |= self.kb_update()
            refresh |= self.action_update()

            if refresh:
                pygame.display.update()

            time.sleep(0.1)

        pygame.quit()
