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
            try:
                wiring = json.loads(f.read())
            except Exception:
                print(f'Error loading {wiring_file}')
                raise

        wirings = wiring['layouts']

        print(wirings)

        if len(wirings) == 1 and layout is None:
            layout = list(wirings.keys())[0]

        if layout not in wirings:
            raise RuntimeError(
                'missing/invalid layout.  '
                'valid layouts: %s' % ', '.join(wirings.keys()))

        self.layout_name = layout
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
            next_h = 1
            col = 0

            for item in row:
                if isinstance(item, dict):
                    if 'w' in item:
                        next_w = item['w']
                    if 'x' in item:
                        xpos += item['x']
                    if 'h' in item:
                        next_h = item['h']
                else:
                    w = next_w
                    h = next_h
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

    def program(self, callback=None):
        total_items = len(self.dirtymap)
        programmed = 0

        for item, value in self.dirtymap.items():
            layer, row, col = map(int, item.split(':'))
            self.keyboard.set_key(layer, row, col, value)
            self.map[layer][row][col] = value
            programmed += 1
            if callback:
                percent = programmed / total_items
                callback(percent)

        self.dirtymap = {}

    def restore(self, input_file):
        with open(input_file, 'r') as f:
            lines = f.read().split('\n')

        layout = lines[0]
        lines = lines[1:]

        if layout != self.layout_name:
            # there might be some kind of conversion that could
            # be attempted
            raise RuntimeError(
                f'This layout is for {layout}, not {self.layout_name}')

        lines = [line.strip()
                 for line in lines
                 if line.strip() != '' and line[0] != '#']

        if len(lines) != len(self.wiring) * self.layers:
            raise RuntimeError(f'Wrong number of rows/layers')

        layer = 0
        row = 0
        keypos = 0
        for line in lines:
            keycodes = [int(x.strip()) for x in line.split(',')]
            for col, keycode in enumerate(keycodes):
                map_row, map_col = self.wiring[row][col]
                old_keycode = self.map[layer][map_row][map_col]
                if keycode != old_keycode:
                    idx = f'{layer}:{map_row}:{map_col}'
                    self.dirtymap[idx] = keycode
                    old_key = keys.bytes_to_key.get(old_keycode, old_keycode)
                    new_key = keys.bytes_to_key.get(keycode, keycode)
                    keylabel = self.keylist[keypos].get('label', 'unknown')

                    self.logger.info(f'{idx} ({keylabel}) was {old_key}, updating to {new_key}')
                keypos += 1

            row += 1
            if row >= len(self.wiring):
                layer += 1
                row = 0
                keypos = 0

        assert row == 0
        assert layer == self.layers

        print(f'{len(self.dirtymap)} items changed')


    def backup(self, output_file):
        with open(output_file, 'w') as f:
            f.write(f'{self.layout_name}\n')
            for layer in range(self.layers):
                f.write(f'#\n# LAYER {layer}\n#\n')

                for row in self.wiring:
                    label_vals = []
                    key_vals = []

                    for col in row:
                        row_idx, col_idx = col
                        key = self.map[layer][row_idx][col_idx]
                        key_vals.append(key)
                        label_vals.append(keys.label_for_keycode(key))

                    f.write('# ' + ', '.join(
                        f'{l:>7}' for l in label_vals) + '\n')
                    f.write('  ' + ', '.join(
                        f'{str(k):>7}' for k in key_vals) + '\n')

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
