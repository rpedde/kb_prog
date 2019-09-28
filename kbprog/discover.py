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
    },
    '1209:6060:v6801': {
        'name': 'Pedde Heavy Industries r68/rev1',
        'tag': 'r68rev1',
        'rows': 5,
        'cols': 15
    },
    '1209:6060:v1701': {
        'name': 'Pedde Heavy Industries r17/rev1',
        'tag': 'r17rev1',
        'rows': 5,
        'cols': 4
    },
    '1209:6060:v6001': {
        'name': 'Pedde Heavy Industries r60/rev1',
        'tag': 'r60rev1',
        'rows': 5,
        'cols': 14
    }

}


def discover(match=None):
    devs = usb.core.find(find_all=True)
    results = []

    for device in devs:
        did = '%04x:%04x' % (device.idVendor, device.idProduct)
        did_ver = '%04x:%04x:v%04x' % (device.idVendor,
                                       device.idProduct,
                                       device.bcdDevice)

        device_info = devices.get(did_ver, devices.get(did))

        if device_info is not None:
            if 'discover_version' in device_info:
                if device.bcdDevice != device_info['discover_version']:
                    continue

            add = True
            if match is not None:
                if match not in device_info['name'] and \
                   match not in device_info['tag']:
                    add = False

            if add:
                struct = device_info
                struct['device'] = device
                struct['id'] = did

                results.append(struct)

    return results


if __name__ == '__main__':
    print(discover())
