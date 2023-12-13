"""
This is where the implementation of the plugin code goes.
The Undo-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('Undo')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Undo(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        logger.debug('path: {0}'.format(core.get_path(active_node)))
        logger.info('name: {0}'.format(core.get_attribute(active_node, 'name')))
        logger.warn('pos : {0}'.format(core.get_registry(active_node, 'position')))
        logger.error('guid: {0}'.format(core.get_guid(active_node)))

        # Undo
        core.set_attribute(active_node, 'name', 'discarded_state')

