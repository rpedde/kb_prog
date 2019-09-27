import logging

import usb.util


class Keyboard(object):
    # -- start commands
    # protocol "alpha"
    COMMAND_START = 0x00
    GET_PROTOCOL_VERSION = 0x01
    GET_KEYBOARD_VALUE = 0x02
    SET_KEYBOARD_VALUE = 0x03
    DYNAMIC_KEYMAP_GET_KEYCODE = 0x04
    DYNAMIC_KEYMAP_SET_KEYCODE = 0x05
    DYNAMIC_KEYMAP_CLEAR_ALL = 0x06
    BACKLIGHT_CONFIG_SET_VALUE = 0x07
    BACKLIGHT_CONFIG_GET_VALUE = 0x08
    BACKLIGHT_CONFIG_SAVE = 0x09
    EEPROM_RESET = 0x0a
    BOOTLOADER_JUMP = 0x0b

    # protocol "beta"
    DYNAMIC_KEYMAP_MACRO_GET_COUNT = 0x0c
    DYNAMIC_KEYMAP_MACRO_GET_BUFFER_SIZE = 0x0d
    DYNAMIC_KEYMAP_MACRO_GET_BUFFER = 0x0e
    DYNAMIC_KEYMAP_MACRO_SET_BUFFER = 0x0f
    DYNAMIC_KEYMAP_MACRO_RESET = 0x10
    DYNAMIC_KEYMAP_GET_LAYER_COUNT = 0x11
    DYNAMIC_KEYMAP_GET_BUFFER = 0x12
    DYNAMIC_KEYMAP_SET_BUFFER = 0x13
    # -- end commands

    # -- start backlight values ids
    # protocol "alpha"
    BACKLIGHT_USE_SPLIT_BACKSPACE = 0x01
    BACKLIGHT_USE_SPLIT_LEFT_SHIFT = 0x02
    BACKLIGHT_USE_SPLIT_RIGHT_SHIFT = 0x03
    BACKLIGHT_USE_7U_SPACEBAR = 0x04
    BACKLIGHT_USE_ISO_ENTER = 0x05
    BACKLIGHT_DISABLE_HHKB_BLOCKER_LEDS = 0x06
    BACKLIGHT_DISABLE_WHEN_USB_SUSPENDED = 0x07
    BACKLIGHT_DISABLE_AFTER_TIMEOUT = 0x08
    BACKLIGHT_BRIGHTNESS = 0x09
    BACKLIGHT_EFFECT = 0x0a
    BACKLIGHT_EFFECT_SPEED = 0x0b
    BACKLIGHT_COLOR_1 = 0x0c
    BACKLIGHT_COLOR_2 = 0x0d
    BACKLIGHT_CAPS_LOCK_INDICATOR_COLOR = 0x0e
    BACKLIGHT_CAPS_LOCK_INDICATOR_ROW_Col = 0x0f
    BACKLIGHT_LAYER_1_INDICATOR_COLOR = 0x10
    BACKLIGHT_LAYER_1_INDICATOR_ROW_COL = 0x11
    BACKLIGHT_LAYER_2_INDICATOR_COLOR = 0x12
    BACKLIGHT_LAYER_2_INDICATOR_ROW_COL = 0x13
    BACKLIGHT_LAYER_3_INDICATOR_COLOR = 0x14
    BACKLIGHT_LAYER_3_INDICATOR_ROW_COL = 0x15
    BACKLIGHT_ALPHAS_MODS = 0x16

    # protocol "beta"
    BACKLIGHT_CUSTOM_COLOR = 0x17
    # -- end backlight values ids

    PROTOCOLS = {
        7: 'alpha',
        8: 'beta',
        9: 'gamma'
    }

    BL_PROTOCOLS = {
        0: 'none',
        1: 'wilba'
    }

    def __init__(self, device, name, tag, rows, cols):
        self.name = name
        self.tag = tag
        self.rows = rows
        self.cols = cols
        self.device = device

        self.logger = logging.getLogger(__name__)

        self.find_endpoint()
        self._layers = None

        if self.device.is_kernel_driver_active(self.interface):
            self.device.detach_kernel_driver(self.interface)

        try:
            usb.util.claim_interface(self.device, self.interface)
            self.logger.info('Claimed device')
        except Exception as e:
            self.logger.debug('Could not claim device: %s',
                              str(e))

        self.protocol = self.get_protocol()

    def dump(self):
        self.logger.info('Name: %s', self.name)
        self.logger.info('Wiring: %sx%s', self.cols, self.rows)

        protocol = self.PROTOCOLS.get(self.protocol,
                                      'Unknown: %d' % self.protocol)
        self.logger.info('Protocol: %s', protocol)
        self.logger.info('Layers: %s', self.layers)

    def get_protocol(self):
        result = self._send_command(self.GET_PROTOCOL_VERSION)
        return (result[1] * 256) + result[2]

    def bootloader(self):
        self._send_command(self.BOOTLOADER_JUMP)

    def save(self):
        self._send_command(self.BACKLIGHT_CONFIG_SAVE)

    @property
    def layers(self):
        if self._layers is None:
            if self.protocol == 7:
                self._layers = 3
            result = self._send_command(self.DYNAMIC_KEYMAP_GET_LAYER_COUNT)
            self._layers = result[1]
        return self._layers

    def set_key(self, layer, row, col, value):
        self._send_command(
            self.DYNAMIC_KEYMAP_SET_KEYCODE,
            layer, row, col, (value & 0xFF00) >> 8, value & 0xFF)

    def keyboard_map(self, callback=None):
        items = []

        total_items = self.layers * self.rows * self.cols
        read = 0

        for layer in range(self.layers):
            items.append([])

            for row in range(self.rows):
                items[layer].append([])
                self.logger.debug('Reading layer %d, row %d' % (layer, row))

                for col in range(self.cols):
                    result = self._send_command(
                        self.DYNAMIC_KEYMAP_GET_KEYCODE,
                        layer, row, col)
                    items[layer][row].append(result[4] * 256 + result[5])
                    read += 1

                    if callback is not None:
                        percent = float(read) / float(total_items)
                        callback(percent)

        return items

    @property
    def effect(self):
        result = self._send_command(self.BACKLIGHT_CONFIG_GET_VALUE,
                                    self.BACKLIGHT_EFFECT, 0x00)
        return result[2]

    @effect.setter
    def effect(self, value):
        self._send_command(self.BACKLIGHT_CONFIG_SET_VALUE,
                           self.BACKLIGHT_EFFECT, value)

    def _send_command(self, cmd, *args):
        bytedata = bytearray([cmd] + list(args))

        self.logger.debug('Send: %d bytes: %s',
                          len(bytedata),
                          ' '.join('%02x' % x for x in bytedata))
        self.device.write(self.out_ep, bytedata)
        result = self.device.read(self.in_ep, 32)
        self.logger.debug('Recv: %s bytes: %s',
                          len(result),
                          ' '.join('%02x' % x for x in result))
        return result

    def find_endpoint(self):
        self.logger.debug('Probing for endpoint')

        cfg = self.device.get_active_configuration()
        for intf in cfg:
            self.logger.debug('Iface %s', intf.bInterfaceNumber)

            ep_addrs = []

            for ep in intf:
                ep_addrs.append(ep.bEndpointAddress)
                self.logger.debug('  %s', ep.bEndpointAddress)

            if len(ep_addrs) == 2:
                ep1 = ep_addrs[0]
                ep2 = ep_addrs[1]

                self.out_ep = ep1 if ep1 < 0x7f else ep2
                self.in_ep = ep2 if self.out_ep == ep1 else ep1
                self.interface = intf.bInterfaceNumber

                self.logger.info('Using interface %d: in %d/out %d',
                                 self.interface, self.in_ep, self.out_ep)

        if not self.interface:
            raise RuntimeError('Cannot find reasonable interface')
