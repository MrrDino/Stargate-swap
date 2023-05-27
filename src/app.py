from loguru import logger

from bridge_swap import Web3Client
from constants import USDC, AVAX

import yaml
import os


try:
    with open(os.path.join(os.path.dirname(os.getcwd()), 'configs', 'config.yaml')) as file:
        config = yaml.safe_load(file)
except Exception as err:
    logger.error(err)


def start():
    w = Web3Client(
        sender_node=config['AVALANCHE_NODE'],
        receive_node=config['POLYGON_NODE'],
        private_key=config['PRIVATE_KEY'],
        wallet=config['WALLET_ADDRESS']
    )
    w.make_swap(
        token_0=USDC,
        token_1=AVAX,
        send_network='Avalanche',
        receive_network='Polygon'
    )


if __name__ == '__main__':
    start()
