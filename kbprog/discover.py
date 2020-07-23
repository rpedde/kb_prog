import hid
import usb.core

devices = {
    '5241:080a': {
        'name': 'Rama U80-A',
        'tag': 'u80a',
        'rows': 6,
        'cols': 17
    },
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
    },
    '1209:6060:v6004': {
        'name': 'Pedde Heavy Industries r60/rev4',
        'tag': 'r60rev4',
        'rows': 5,
        'cols': 14
    },
    '1209:6060:v6501': {
        'name': 'TX-65',
        'tag': 'tx65',
        'rows': 5,
        'cols': 16
    },
    '5053:434e': {
        'name': 'Percent Canoe',
        'tag': 'canoe',
        'rows': 5,
        'cols': 15
    },
    'feed:6050': {
        'name': 'TX-65',
        'tag': 'tx65',
        'rows': 5,
        'cols': 16
    }
}


def discover(match=None, use_hid=False):
    if not use_hid:
        return old_discover(match=match)
    return new_discover(match=match)


def new_discover(match=None):
    devs = hid.enumerate()
    results = []

    results_by_tag = {}

    for d in devs:
        did = f"{d['vendor_id']:04x}:{d['product_id']:04x}"
        did_ver = f"{did}:v{d['release_number']:04x}"

        device_info = devices.get(did_ver, devices.get(did))

        if device_info is not None:
            add = True
            if match is not None:
                if match not in device_info['name'] and \
                   match not in device_info['tag']:
                    add = False

            if add:
                if device_info['tag'] not in results_by_tag:
                    struct = device_info
                    struct['device'] = [d['path']]
                    struct['id'] = did
                    struct['use_hid'] = True
                    results_by_tag[device_info['tag']] = struct
                else:
                    kb = results_by_tag[device_info['tag']]
                    kb['device'].append(d['path'])

    return list(results_by_tag.values())


def old_discover(match=None):
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
                struct['use_hid'] = False

                results.append(struct)

    return results


if __name__ == '__main__':
    print(discover())
