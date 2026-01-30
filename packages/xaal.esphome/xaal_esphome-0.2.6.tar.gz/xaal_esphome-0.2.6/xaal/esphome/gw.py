from xaal.lib import tools
from xaal.schemas import devices
from . import bindings

import logging
import platform

PACKAGE_NAME = 'xaal.esphome'
logger = logging.getLogger(PACKAGE_NAME)

# disable internal logging
logging.getLogger("tzlocal").setLevel(logging.WARNING)


class GW(object):
    def __init__(self, engine):
        self.engine = engine
        # ESPDevice dict
        self.devices = {}
        self.config()
        self.engine.on_stop(self._exit)
        self.engine.on_start(self.start)

    def config(self):
        cfg = tools.load_cfg(PACKAGE_NAME)
        if not cfg:
            cfg = tools.new_cfg(PACKAGE_NAME)
            cfg['devices'] = {}
            logger.warning("Created an empty config file")
            cfg.write()
        self.cfg = cfg

    async def start(self):
        self.setup()
        self.setup_gw()

    def setup(self):
        cfg = self.cfg
        devs = cfg['devices']
        for ip in devs:
            base_addr = devs[ip].get('base_addr', None)
            if not base_addr:
                base_addr = tools.get_random_base_uuid(9)
                devs[ip]['base_addr'] = base_addr
            dev = bindings.ESPDevice(self.engine, ip, devs[ip])
            self.devices[ip] = dev
            self.engine.new_task(dev.loop())

    def setup_gw(self):
        addr = tools.get_uuid(self.cfg['config']['addr'])
        gw = devices.gateway(addr)
        gw.vendor_id = 'Rambo'
        gw.product_id = 'ESPHome GW'
        gw.info = "%s@%s" % (PACKAGE_NAME, platform.node())
        gw.version = 0.1
        gw.unsupported_attributes.append('inactive')
        self.gw = gw
        self.engine.add_device(gw)
        # we update embedded devices periodically, not the best option
        # but I don't want to keep fine track this because it can
        # change as soon as you reflash an ESP.
        self.engine.add_timer(self.update_embedded, 10)

    def update_embedded(self):
        emb = []
        for esp in self.devices.values():
            for k in esp.embedded:
                emb.append(k.dev.address)
        self.gw.attributes['embedded'] = emb

    def _exit(self):
        """save config on exit (mainly base_addr)"""
        cfg = tools.load_cfg(PACKAGE_NAME)
        if cfg != self.cfg:
            logger.info('Saving configuration file')
            self.cfg.write()


def setup(eng):
    GW(eng)
    return True
