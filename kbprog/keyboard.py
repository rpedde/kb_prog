
import logging

import hid
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

    def __init__(self, device, name, tag, rows, cols, use_hid, **kwargs):
        self.name = name
        self.tag = tag
        self.rows = rows
        self.cols = cols

        self.logger = logging.getLogger(__name__)

        self._layers = None
        self._macro_buffer_size = None
        self._macro_count = None
        self.macros = []

        self.use_hid = use_hid
        self.device = device

        if not self.use_hid:
            self.find_endpoint()

            if self.device.is_kernel_driver_active(self.interface):
                self.device.detach_kernel_driver(self.interface)

            try:
                usb.util.claim_interface(self.device, self.interface)
                self.logger.info('Claimed device')
            except Exception as e:
                self.logger.debug('Could not claim device: %s',
                                  str(e))
        else:
            self.find_hidpath()

        self.protocol = self.get_protocol()
        self._load_macros()

    def dump(self):
        self.logger.info('Name: %s', self.name)
        self.logger.info('Wiring: %sx%s', self.cols, self.rows)

        protocol = self.PROTOCOLS.get(self.protocol,
                                      'Unknown: %d' % self.protocol)
        self.logger.info('Protocol: %s', protocol)
        self.logger.info('Layers: %s', self.layers)
        self.logger.info('Macros: %s', self.macro_count)
        if self.macro_count:
            self.logger.info('Macro buffer size: %s', self.macro_bytes)
            for idx, macro in enumerate(self.macros):
                self.logger.info('Macro %d: %s', idx, macro)

    def get_protocol(self):
        result = self._send_command(self.GET_PROTOCOL_VERSION)
        retval = (result[1] * 256) + result[2]
        return retval

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

    @property
    def macro_bytes(self):
        if self.protocol == 7:
            self._macro_buffer_size = 0
        else:
            result = self._send_command(
                self.DYNAMIC_KEYMAP_MACRO_GET_BUFFER_SIZE)
            self._macro_buffer_size = result[1] << 8 | result[2]
        return self._macro_buffer_size

    @property
    def macro_count(self):
        if self.protocol == 7:
            self._macro_count = 0
        else:
            result = self._send_command(self.DYNAMIC_KEYMAP_MACRO_GET_COUNT)
            self._macro_count = result[1]
        return self._macro_count

    def set_macro(self, index, value):
        if index > self.macro_count:
            raise RuntimeError('Macro %d out of range' % index)

        value = bytes(value, 'latin1').decode('unicode_escape')
        self.macros[index] = value

    def _load_macros(self):
        if self.macro_count == 0:
            return

        macro_bytes = self.macro_bytes
        if not macro_bytes:
            return

        buffer = bytearray()
        left_to_read = macro_bytes
        offset = 0

        while(left_to_read):
            to_read = min(left_to_read, 28)
            next = self._send_command(
                self.DYNAMIC_KEYMAP_MACRO_GET_BUFFER,
                (offset & 0xFF00) >> 8,
                offset & 0xFF,
                to_read & 0xFF)

            data = next[4:4+to_read]
            buffer += data
            left_to_read -= to_read
            offset += to_read

        macro = 0
        current_macro = bytearray()
        offset = 0

        while(macro < self.macro_count):
            if buffer[offset] != 0:
                current_macro.append(buffer[offset])
            else:
                self.logger.debug('Macro %d: %s', macro, current_macro)
                self.macros.append(current_macro.decode('latin1'))
                current_macro = bytearray()
                macro += 1

            offset += 1

    def save_macros(self):
        macro_bytes = self.macro_bytes
        if not macro_bytes:
            return

        buffer = bytearray()
        for macro in range(self.macro_count):
            buffer += bytearray(self.macros[macro].encode('latin1'))
            buffer.append(0)

        if len(buffer) > self.macro_bytes:
            raise RuntimeError('macro too large')

        left_to_write = len(buffer)
        offset = 0

        while(left_to_write):
            to_write = min(left_to_write, 28)
            self._send_command(
                self.DYNAMIC_KEYMAP_MACRO_SET_BUFFER,
                (offset & 0xFF00) >> 8,
                offset & 0xFF,
                to_write & 0xFF,
                buffer[offset:offset+to_write])

            left_to_write -= to_write
            offset += to_write

    def set_key(self, layer, row, col, value):
        self._send_command(
            self.DYNAMIC_KEYMAP_SET_KEYCODE,
            layer, row, col, (value & 0xFF00) >> 8, value & 0xFF)

    def keyboard_map_beta(self, callback=None):
        buffer = bytearray()

        buffer_size = self.layers * self.rows * self.cols * 2
        left_to_read = buffer_size
        offset = 0

        while(left_to_read):
            to_read = min(left_to_read, 28)
            next = self._send_command(
                self.DYNAMIC_KEYMAP_GET_BUFFER,
                (offset & 0xFF00) >> 8,
                offset & 0xFF,
                to_read & 0xFF)

            data = next[4:4+to_read]
            buffer += data
            left_to_read -= to_read
            offset += to_read

            if callback is not None:
                read = buffer_size - left_to_read
                percent = float(read) / float(buffer_size)
                callback(percent)

        self.logger.debug('Map: %s bytes (expected %s): %s',
                          len(buffer),
                          self.layers * self.rows * self.cols * 2,
                          ' '.join('%02x' % x for x in buffer))

        # now, split it out
        items = []
        pos = 0
        for layer in range(self.layers):
            items.append([])
            for row in range(self.rows):
                items[layer].append([])
                for col in range(self.cols):
                    items[layer][row].append(
                        buffer[pos] << 8 | buffer[pos+1])
                    pos += 2

        return items

    def keyboard_map(self, callback=None):
        if self.protocol > 7:  # beta or better
            return self.keyboard_map_beta(callback=callback)

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

    def _send_command(self, *args):
        bufsize = 32
        out_buf = [0x00] * bufsize
        ofs = 0

        for item in args:
            if isinstance(item, int):
                out_buf[ofs] = item
                ofs += 1
            elif isinstance(item, str):
                for char in item:
                    out_buf[ofs] = ord(char)
                    ofs += 1
            elif isinstance(item, bytearray):
                for char in item:
                    out_buf[ofs] = char
                    ofs += 1
            else:
                raise RuntimeError('bad cmd')

        out_buf = (''.join([chr(x) for x in out_buf])).encode('latin1')
        if len(out_buf) != 32:
            raise RuntimeError('Buffer too big!')

        self.logger.debug('Send: %d bytes: %s',
                          len(out_buf),
                          ' '.join('%02x' % x for x in out_buf))

        if not self.use_hid:
            result = self.device.write(self.out_ep, out_buf, timeout=1000)

        retry_count = 0
        while retry_count <= 1:
            if self.use_hid:
                result = self.hid_device.write(out_buf)
                in_buf = self.hid_device.read(32, 300)  # 1s timeout
            else:
                in_buf = self.device.read(self.in_ep, 32, timeout=1000)

            if len(in_buf) != 0:
                break
            retry_count += 1
            self.logger.info('Bad read... retrying...')

        self.logger.debug('Recv: %s bytes: %s',
                          len(in_buf),
                          ' '.join('%02x' % x for x in in_buf))
        return in_buf

    def find_hidpath(self):
        self.logger.info(f'Probing for raw hid device among {self.device}')
        for item in self.device:
            self.hid_device = hid.Device(path=item)
            try:
                buf = self._send_command(self.GET_PROTOCOL_VERSION)
                pver = buf[1] * 256 + buf[2]
            except Exception:
                self.logger.info(f'Timeout for {item}')
                self.hid_device.close()
                continue

            if pver not in self.PROTOCOLS:
                self.logger.info(f'Invalid protocol: {pver}')
            else:
                self.logger.info(f'Using path {item}')
                return

        raise RuntimeError('Cannot find suitable hid device')

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
            raise RuntimeError('No good interface found')
