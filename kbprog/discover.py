import usb.core

devices = {
    '5241:060a': {
        'name': 'Rama M60-A',
        'tag': 'm60a',
        'rows': 5,
        'cols': 15
    },
    '5241:006b': {
        'name': 'Rama M6-B',
        'tag': 'm6b',
        'rows': 1,
        'cols': 6
    },
    '5241:4b59': {
        'name': 'Rama Koyu',
        'tag': 'koyu',
        'rows': 5,
        'cols': 15
    }
}


def discover(match=None):
    devs = usb.core.find(find_all=True)
    results = []

    for device in devs:
        did = '%04x:%04x' % (device.idVendor, device.idProduct)

        if did in devices:
            add = True
            if match is not None:
                if match not in devices[did]['name'] and \
                   match not in devices[did]['tag']:
                    add = False

            if add:
                struct = devices[did]
                struct['device'] = device
                struct['id'] = did

                results.append(struct)

    return results


if __name__ == '__main__':
    print(discover())
