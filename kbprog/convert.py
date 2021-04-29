#!/usr/bin/env python

""" Quick and dirty keymap parser for converting qmk keyboards """

import argparse
import json
import os
import re
import sys


qmk_root = '~/working/electronics/software/qmk_firmware'


def get_parser():
    parser = argparse.ArgumentParser(description='keymap converter')
    parser.add_argument('--qmk-root', default=qmk_root)
    parser.add_argument('--wiring-path')
    parser.add_argument('keyboard', help='keyboard mfg/flavor')
    parser.add_argument('--map', action='append')
    parser.add_argument('--skip', action='append')
    return parser


def get_kb_info(kb_root, extra_maps=None, skips=None):
    if skips is None:
        skips = []

    kb_name = os.path.split(kb_root)[-1]

    header_file = os.path.expanduser(os.path.join(kb_root, kb_name + '.h'))
    config_file = os.path.expanduser(os.path.join(kb_root, 'config.h'))
    layout_dir = os.path.join(os.path.dirname(__file__), 'layouts')

    conf = {}

    with open(config_file, 'r') as f:
        for line in f.readlines():
            result = re.match('^#define\s+([^\s]+)\s+(.*)$', line)
            if result:
                conf[result[1].lower()] = result[2]

    if conf['vendor_id'].startswith('0x'):
        conf['vendor_id'] = conf['vendor_id'][2:]

    if conf['product_id'].startswith('0x'):
        conf['product_id'] = conf['product_id'][2:]

    conf['vendor_id'] = conf['vendor_id'].lower()
    conf['product_id'] = conf['product_id'].lower()

    discover_entry = {
        'name': '{manufacturer} {product}'.format(**conf),
        'tag': conf['product'].lower(),
        'rows': int(conf['matrix_rows']),
        'cols': int(conf['matrix_cols']),
        'id': '{vendor_id}:{product_id}'.format(**conf)
    }
    discover_id = '{vendor_id}:{product_id}'.format(**conf)

    print(f'{discover_id} = {discover_entry}')

    # now read the layouts
    in_define = False
    all_defines = []

    kc_no_aliases = []

    with open(header_file, 'r') as f:
        current_define = ''
        for line in f.readlines():
            line = line.strip()
            if line:
                if re.match('^\s*#define\s+LAYOUT.*$', line):
                    in_define = True

                if in_define:
                    if line.endswith('\\'):
                        current_define += line[:-1]
                    else:
                        in_define = False
                        current_define += line
                        all_defines.append(current_define)
                        current_define = ''
                else:
                    kcno = re.match('^\s*#define\s+(^\s)\s+KC_NO.*$', line)
                    if kcno:
                        kc_no_aliases.append(kcno[1].strip())

    layouts = {}
    print(f'attempting decode of {len(all_defines)} layouts')

    # matrix_size = discover_entry['rows'] * discover_entry['cols']
    for layout in all_defines:
        result = re.match('^\s*#define\s+([^\(]+)\((.*)\)(.*)$', layout)
        if not result:
            print(f'whoops.. failed to parse {layout}')
        else:
            layout_name = result[1]
            if result[1].startswith('LAYOUT_'):
                layout_name = result[1][7:]

            keys = [x.strip() for x in result[2].split(',')]
            keys = [x for x in keys if x not in skips]
            # if len(keys) != discover_entry['rows'] * discover_entry['cols']:
            #     print(f'bad keys in {layout_name}: {len(keys)} != {matrix_size}')
            # print(f'name: {result[1]}')
            # print(f'keys: {result[2]}')
            raw_values = result[3].strip()

            result = re.findall(r'{[^}]+}', raw_values[1:-1])

            if not result:
                print('bad values in {layout_name}')
                continue
            else:
                rows = [[x.strip() for x in y[1:-1].split(',')] for y in result]

            if len(rows) != discover_entry['rows']:
                print(f'Not enough rows in layout {layout_name}')
                continue

            if not all(len(x) == discover_entry['cols'] for x in rows):
                print(f'Not enough cols in layout {layout_name}')

            # invert the map
            imap = {}
            for rowidx, row in enumerate(rows):
                for colidx, key in enumerate(row):
                    imap[key] = [rowidx, colidx]

            layout_map = {'60_ansi': '60',
                          '65_ansi_blocker': '68-compat',
                          '65_ansi': '68-compat',  # not quite right, but close enough
                          'tkl_ansi': 'tkl',
                          '96_ansi': '96'}
            if extra_maps:
                layout_map.update(extra_maps)

            if layout_name in layout_map:
                print(f'mapping {layout_name}->{layout_map[layout_name]}')
                layout_name = layout_map[layout_name] + '.json'

            layout_path = os.path.join(layout_dir, layout_name)
            if not os.path.exists(layout_path):
                print(f'cannot find layout {layout_name}')
                continue

            with open(layout_path, 'r') as f:
                layout_data = json.loads(f.read())

            layout_data = [[x for x in row if not isinstance(x, dict)] for row in layout_data]
            layout_len = sum(len(x) for x in layout_data)

            if layout_len != len(keys):
                print(f'layout has {layout_len} keys, but map has {len(keys)}')
                continue

            this_layout = []
            pos = 0
            for row_idx, row in enumerate(layout_data):
                this_row = []
                for col_idx, _ in enumerate(row):
                    key = keys[pos]

                    if skips and key in skips:
                        continue

                    this_row.append(imap[key])
                    if key not in imap:
                        print(f'cant find key {key} at ({row_idx}, {col_idx})')
                        raise RuntimeError

                    pos += 1
                this_layout.append(this_row)

            layouts[layout_name.replace('.json', '')] = this_layout

    return discover_entry, layouts


def main():
    args = get_parser().parse_args()

    extra_maps = None
    if args.map:
        extra_maps = {x.split(':')[0]: x.split(':')[1] for x in args.map}

    kb_root = os.path.expanduser(os.path.join(args.qmk_root, 'keyboards', args.keyboard))
    discover, wiring = get_kb_info(kb_root, extra_maps, args.skip)

    d_id = discover.pop('id')

    print(f'Discover info: {repr(d_id)}: {repr(discover)}')
    if args.wiring_path:
        with open(args.wiring_path, 'w') as f:
            f.write(json.dumps(wiring))

        print(f'wrote wiring to {args.wiring_path}')
    else:
        print(json.dumps({"layouts": wiring}))


if __name__ == '__main__':
    sys.exit(main())
