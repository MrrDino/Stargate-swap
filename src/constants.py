MATIC = "0x0000000000000000000000000000000000001010"
USDC = "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E"
AVAX = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"

ROUTERS = {
    'Ethereum': '0x8731d54E9D02c286767d56ac03e8037C07e01e98',
    'BnbChain': '0x4a364f8c717cAAD9A442737Eb7b8A55cc6cf18D8',
    'Avalanche': '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd',
    'Polygon': '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd',
    'Arbitrum': '0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614',
    'Optimism': '0xB0D502E938ed5f4df2E681fE6E419ff29631d62b',
    'Fantom': '0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6',
}

DEFAULT_GAS = 700000
COEFFICIENT = .77  # в зависимости от загруженности моста меняется коэффициент (процент от обзей суммы матиков)
NETWORK_LOAD = 1.21  # при загруженности сети необходимо повышать, для увеличения газа
SLIPPAGE = 5

NETWORKS = {
    'Ethereum': 101,
    'BNB': 102,
    'Avalanche': 106,
    'Polygon': 109,
    'Arbitrum': 110,
    'Optimism': 111,
    'Fantom': 112,
    'Metis': 151,
}

TOKEN_POOLS = {
    "Avalanche": {
        'USDC': 1,
        'USDT': 2,
        'FRAX': 7,
        'MAI': 16,
    },
    'Polygon': {
        'USDC': 1,
        'USDT': 2,
        'DAI': 3,
        'MAI': 16
    }
}
