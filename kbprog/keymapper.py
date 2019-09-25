import json
import logging
import os

from kbprog import keys


class Keymapper(object):
    def __init__(self, keyboard, layout=None):
        self.keyboard = keyboard
        self.logger = logging.getLogger(__name__)
        self.map = None
        self.dirtymap = {}

        wiring_path = os.path.join(
            os.path.dirname(__file__),
            'wiring')

        layout_path = os.path.join(
            os.path.dirname(__file__),
            'layouts')

        wiring_file = os.path.join(
            wiring_path, '%s.json' % keyboard.tag)

        if not os.path.exists(wiring_file):
            raise RuntimeError(
                'Unknown wiring for %s' % keyboard.tag)

        with open(wiring_file, 'r') as f:
            wiring = json.loads(f.read())

        wirings = wiring['layouts']

        print(wirings)

        if len(wirings) == 1 and layout is None:
            layout = list(wirings.keys())[0]

        if layout not in wirings:
            raise RuntimeError(
                'missing/invalid layout.  '
                'valid layouts: %s' % ', '.join(wirings.keys()))

        self.wiring = wirings[layout]

        layout_file = os.path.join(
            layout_path, '%s.json' % layout)

        with open(layout_file, 'r') as f:
            self.layout = json.loads(f.read())

        self.keylist = []
        self.rows = len(self.layout)

        max_x = 0
        ypos = 0

        for row in self.layout:
            xpos = 0
            next_w = 1
            col = 0

            for item in row:
                if isinstance(item, dict):
                    if 'w' in item:
                        next_w = item['w']
                    if 'x' in item:
                        xpos += item['x']
                else:
                    w = next_w
                    h = 1
                    labels = item.split('\n')
                    if len(labels) == 1:
                        label = labels[0]
                        shift_label = ''
                    else:
                        label = labels[1]
                        shift_label = labels[0]

                    keyinfo = {'x': xpos,
                               'y': ypos,
                               'wiremap': self.wiring[ypos][col],
                               'label': self.label_for(label),
                               'shift_label': self.label_for(shift_label),
                               'w': w,
                               'h': h}

                    keyinfo['found'] = False

                    self.keylist.append(keyinfo)

                    if xpos + w > max_x:
                        max_x = xpos + w

                    xpos += next_w
                    next_w = 1
                    col += 1

            ypos += 1

        self.cols = ypos
        self.max_x = max_x
        self.max_y = ypos

    def is_dirty(self, layer, keyinfo):
        row, col = keyinfo['wiremap']
        idx = '%s:%s:%s' % (layer, row, col)

        if idx in self.dirtymap:
            return True

        return False

    def set_key(self, layer, keyinfo, newcode):
        row, col = keyinfo['wiremap']
        idx = '%s:%s:%s' % (layer, row, col)

        self.dirtymap[idx] = keys.key_to_bytes[newcode]

    def label_for_key(self, layer, keyinfo):
        if self.map is None:
            return '?'

        row, col = keyinfo['wiremap']

        idx = '%s:%s:%s' % (layer, row, col)

        if idx in self.dirtymap:
            key = self.dirtymap[idx]
        else:
            key = self.map[layer][row][col]

        label = keys.label_for_keycode(key)
        return label

    def label_for(self, what):
        return what

    def get_map(self, callback=None):
        self.map = self.keyboard.keyboard_map(callback=callback)

    @property
    def layers(self):
        return self.keyboard.layers

    @property
    def name(self):
        return self.keyboard.name
