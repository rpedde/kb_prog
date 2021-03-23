#!/usr/bin/env python

import argparse
import json
import logging
import sys

from kbprog import discover, keyboard, keys
from kbprog.keymapper import Keymapper
from kbprog.display import ProgramDisplay


def get_parser():
    parser = argparse.ArgumentParser(description='keyboard manager')
    parser.add_argument('--match', '-m')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--hid', action='store_true')

    subparsers = parser.add_subparsers(help='action', dest='action')

    subparsers.add_parser('info', help='dump info')
    subparsers.add_parser('list', help='list devices')
    subparsers.add_parser('bootloader', help='bootloader')
    subparsers.add_parser('map', help='map')

    edit_parser = subparsers.add_parser('edit', help='edit')
    edit_parser.add_argument('--layout', help='key layout format')

    led_parser = subparsers.add_parser('led', help='led settings')

    led_subparsers = led_parser.add_subparsers(help='led subaction',
                                               dest='subaction')

    effects_parser = led_subparsers.add_parser('effect', help='effects')
    effects_parser.add_argument('effect',
                                help='what effect (next/prev/number)')

    macro_parser = subparsers.add_parser('macro', help='set macros')
    macro_parser.add_argument('index', type=int)
    macro_parser.add_argument('value')

    backup_parser = subparsers.add_parser('backup', help='backup key map')
    backup_parser.add_argument('file')
    backup_parser.add_argument('--layout', help='key layout format')


    restore_parser = subparsers.add_parser('restore', help='restore key map')
    restore_parser.add_argument('file')
    restore_parser.add_argument('--layout', help='key layout format')
    restore_parser.add_argument('--dry-run', action='store_true')

    # save_parser = led_subparsers.add_parser('save', help='save')

    return parser


def do_edit(kb, layout):
    keymapper = Keymapper(kb, layout=layout)
    programmer = ProgramDisplay(keymapper)

    programmer.run()


def main(rawargs):
    args = get_parser().parse_args(rawargs)

    fmt = '[%(asctime)s.%(msecs)03d] %(levelname)s [%(name)s:%(lineno)d] %(message)s'
    level = logging.DEBUG if args.debug else logging.INFO

    logging.basicConfig(format=fmt, level=level, datefmt='%Y-%m-%dT%H:%M:%S')

    results = discover.discover(match=args.match, use_hid=args.hid)

    if len(results) == 0:
        logging.error('no results')
        return 0

    if args.action == 'list':
        for item in results:
            logging.info('%s %s (%s)', item['id'], item['name'], item['tag'])
        return 0

    if len(results) > 1:
        logging.error('multiple results: %s',
                      ', '.join(x['tag'] for x in results))
        return 1

    kbinfo = results[0]

    # kb = keyboard.Keyboard(kbinfo['device'],
    #                        kbinfo['tag'],
    #                        kbinfo['name'],
    #                        kbinfo['rows'],
    #                        kbinfo['cols'])
    kb = keyboard.Keyboard(**{k: v for k, v in kbinfo.items() if k != 'id'})

    if args.action == 'edit':
        do_edit(kb, args.layout)
    elif args.action == 'info':
        print(kb.dump())
    elif args.action == 'macro':
        kb.set_macro(args.index, args.value)
        kb.save_macros()
    elif args.action == 'bootloader':
        kb.bootloader()
    elif args.action == 'map':
        kmap = kb.keyboard_map()

        for layer in range(kb.layers):
            logging.info('Layer %d', layer)
            for row in range(kb.rows):
                rowdata = kmap[layer][row]
                logging.info(rowdata)

                pretty = ', '.join(map(keys.label_for_keycode, rowdata))
                logging.info('%s', pretty)

        print(json.dumps(kmap, indent=2))
    elif args.action == 'backup':
        keymapper = Keymapper(kb, layout=args.layout)
        logging.info('getting keyboard map')

        keymapper.get_map()
        keymapper.backup(args.file)

    elif args.action == 'restore':
        keymapper = Keymapper(kb, layout=args.layout)
        logging.info('loading existing map')
        keymapper.get_map()
        keymapper.restore(args.file)
        if not args.dry_run:
            keymapper.program()

    elif args.action == 'led':
        if args.subaction == 'effect':
            current_effect = kb.effect

            logging.debug('Current effect: %d', current_effect)

            if args.effect == 'next':
                if current_effect + 1 > 10:
                    current_effect = 0
            elif args.effect == 'prev':
                if current_effect - 1 < 0:
                    current_effect = 10
            else:
                current_effect = int(args.effect)

            kb.effect = current_effect
        elif args.subaction == 'save':
            kb.save()


if __name__ == '__main__':
    main(sys.argv[1:])
