import asyncio
import logging

from aioesphomeapi import APIClient, APIConnectionError, model

from xaal.lib import Device, tools
from xaal.schemas import devices

logging.getLogger('aioesphomeapi').setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class ESPDevice:
    def __init__(self, engine, ip, cfg):
        self.engine = engine
        self.ip = ip
        self.port = cfg.get('port', 6053)
        self.key = cfg.get('key', None)
        self.passwd = cfg.get('passwd', None)
        addr = tools.get_uuid(cfg.get('base_addr'))
        assert addr, "Invalid base_addr"
        self.base_addr = addr

        self.embedded = []
        self.disconnected = asyncio.Event()
        self.setup()

    def setup(self):
        self.client = APIClient(address=self.ip, port=self.port, password=self.passwd, keepalive=15, noise_psk=self.key)

    async def on_disconnect(self):
        self.disconnected.set()

    def on_change(self, state):
        logger.debug(f'{self.ip}: {state}')
        emb = self.search_embbed(state.key)
        if emb:
            emb.on_change(state)

    def search_embbed(self, key):
        for dev in self.embedded:
            if dev.key == key:
                return dev
        return None

    async def connect(self):
        logger.info(f'Connecting to {self.ip}')
        self.disconnected.clear()
        try:
            await self.client.connect(login=True, on_stop=self.on_disconnect)
            await self.create_embedded()
            self.client.subscribe_states(self.on_change)
        except APIConnectionError as e:
            logger.warning(e)
            await self.client.disconnect(force=True)
            self.disconnected.set()

    async def loop(self):
        await self.connect()
        while 1:
            await self.disconnected.wait()
            await self.client.disconnect()
            await self.remove_embedded()
            await self.connect()

    async def create_embedded(self):
        services = await self.client.list_entities_services()
        # pprint(services)
        group_id = self.base_addr + 0xEEFF
        for serv in services:
            for k in serv:
                klass = find_device_class(k)
                obj = None
                if klass:
                    obj = klass(self, k)

                if obj:
                    obj.dev.group_id = group_id
                    self.engine.add_device(obj.dev)
                    self.embedded.append(obj)
                else:
                    logger.debug(f'No binding class found for {k}')

    async def remove_embedded(self):
        for dev in self.embedded:
            self.engine.remove_device(dev.dev)
        self.embedded = []


def find_device_class(info):
    type_ = type(info)
    if type_ == model.LightInfo:
        return Lamp
    elif type_ == model.SwitchInfo:
        return PowerRelay
    elif type_ == model.SensorInfo:
        if info.device_class == 'signal_strength':
            return WifiMeter
        if info.device_class == 'power':
            return PowerMeter

    elif type_ == model.BinarySensorInfo:
        return Contact
    return None


# ===============================================================================
# Entities bindings
# ===============================================================================
class EntityMixin(object):
    def __init__(self, esp, info):
        self.esp = esp
        self.info = info
        self.dev = None
        self.setup()
        self.setup_device_description()

    @property
    def addr(self):
        return self.esp.base_addr + self.info.key

    @property
    def key(self):
        return self.info.key

    def setup_device_description(self):
        assert self.dev, "Device not setup"
        self.dev.vendor_id = 'ESPHome'
        self.dev.product_id = self.info.object_id
        self.dev.hw_id = self.info.key
        self.dev.info = f'{self.esp.ip}:{self.info.name}'

    def setup(self):
        logger.warning("EntityMixin.setup() not implemented")

    def on_change(self, state):
        logger.warning("EntityMixin.on_change() not implemented")


# ===============================================================================
# Switch
# ===============================================================================
class PowerRelay(EntityMixin):
    def setup(self):
        self.dev = devices.powerrelay_toggle(self.addr)
        self.dev.methods['turn_on'] = self.turn_on
        self.dev.methods['turn_off'] = self.turn_off
        self.dev.methods['toggle'] = self.toggle

    async def turn_on(self):
        await self.esp.client.switch_command(self.info.key, True)

    async def turn_off(self):
        await self.esp.client.switch_command(self.info.key, False)

    async def toggle(self):
        if self.dev.attributes['power']:
            await self.turn_off()
        else:
            await self.turn_on()

    def on_change(self, state):
        self.dev.attributes['power'] = state.state


# ===============================================================================
# Light
# ===============================================================================
class Lamp(EntityMixin):
    # Right now, lamp only support on/off/toggle (lamp.toggle schema), but
    # it could be extended to support brightness, color, etc according to
    # schemas. I don't have anything to test with, so I'll leave it for now.
    # Expect to be extended in the future.
    def setup(self):
        self.dev = devices.lamp_toggle(self.addr)
        self.dev.methods['turn_on'] = self.turn_on
        self.dev.methods['turn_off'] = self.turn_off
        self.dev.methods['toggle'] = self.toggle

    async def turn_on(self):
        await self.esp.client.light_command(self.info.key, True)

    async def turn_off(self):
        await self.esp.client.light_command(self.info.key, False)

    async def toggle(self):
        if self.dev.attributes['light']:
            await self.turn_off()
        else:
            await self.turn_on()

    def on_change(self, state):
        self.dev.attributes['light'] = state.state


# ===============================================================================
# Sensor
# ===============================================================================
class WifiMeter(EntityMixin):
    def setup(self):
        self.dev = Device('wifimeter.basic', self.addr)
        self.dev.new_attribute('rssi')

    def on_change(self, state):
        try:
            self.dev.attributes['rssi'] = int(state.state)
        except ValueError:
            self.dev.attributes['rssi'] = None


class PowerMeter(EntityMixin):
    def setup(self):
        self.dev = devices.powermeter(self.addr)

    def on_change(self, state):
        self.dev.attributes['power'] = round(state.state, 1)


# ===============================================================================
# Binary Sensor
# ===============================================================================
class Contact(EntityMixin):
    def setup(self):
        self.dev = devices.contact(self.addr)

    def on_change(self, state):
        self.dev.attributes['detected'] = state.state
