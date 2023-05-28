from web3.types import Wei, TxParams, ChecksumAddress
from web3.middleware import geth_poa_middleware
from loguru import logger
from web3 import Web3

from abis.stargate_router import ROUTER_ABI
from abis.erc20 import ERC20_ABI

import constants as const

import requests


class Web3Client:

    def __init__(self, sender_node: str, receive_node: str, private_key: str, wallet: str):
        self.binance_url = "https://www.binance.com/api"
        self.receive_node = receive_node
        self.sender_node = sender_node
        self.private_key = private_key
        self.erc_abi = ERC20_ABI
        self.wallet = wallet

    def make_swap(self, token_0: str, token_1: str, send_network: str, receive_network: str):
        """Функция произведения обмена"""

        w3 = self.connect_node(self.sender_node)
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        receive_network = receive_network.capitalize()
        wallet = Web3.to_checksum_address(self.wallet)
        token_0 = Web3.to_checksum_address(token_0)
        token_1 = Web3.to_checksum_address(token_1)
        send_network = send_network.capitalize()
        spender = Web3.to_checksum_address(const.ROUTERS[send_network])

        token_0_bal, token_0_sym = self.get_token_balance(
            abi=self.erc_abi,
            token=token_0,
            wallet=wallet,
            w3=w3
        )

        token_1_bal, token_1_sym = self.get_token_balance(
            abi=self.erc_abi,
            token=token_1,
            wallet=wallet,
            native=True,
            w3=w3
        )

        router = w3.eth.contract(address=spender, abi=ROUTER_ABI)
        w3_2 = self.connect_node(self.receive_node)

        avax_quantity = token_1_bal - w3_2.eth.gas_price * const.DEFAULT_GAS

        logger.info(f"Gas_price: {w3_2.eth.gas_price}")
        logger.info(f"AVAX quantity: {avax_quantity}")

        matic = self.get_matic_quantity(
            token=token_1,
            name=token_1_sym,
            w3=w3,
            token_balance=avax_quantity
        )

        logger.info(f"MATIC quantity: {matic}")

        self.approve_tx(
            gas_price=w3_2.eth.gas_price,
            amount=token_0_bal,
            spender=spender,
            token=token_0,
            signer=wallet,
            w3=w3,
        )

        native_info = {'dstGasForCall': 0, 'dstNativeAmount': matic, 'dstNativeAddr': wallet}

        fee = self.calculate_quote_layer_zero(
            network=receive_network,
            native_info=native_info,
            wallet=wallet,
            router=router
        )

        txn = self.create_swap_tx(
            receive_network=receive_network,
            send_network=send_network,
            native_info=native_info,
            gas_price=w3_2.eth.gas_price,
            amount=token_0_bal,
            token=token_0_sym,
            wallet=wallet,
            router=router,
            fee=int(fee),
            w3=w3
        )

        signed_swap_txn = router.w3.eth.account.sign_transaction(txn, self.private_key)
        logger.success("Транзакция подписана")
        tx = router.w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        logger.success(f"Транзакция отправлена, хэш транзакции: {tx.hex()}")
        logger.info(f"Посмотреть транзакцию: https://snowtrace.io/tx/{tx.hex()}")

    def approve_tx(
            self,
            spender: ChecksumAddress,
            signer: ChecksumAddress,
            token: ChecksumAddress,
            gas_price: int,
            amount: int,
            w3: Web3
    ):
        """Функция утверждения использования средств"""

        token_contract = w3.eth.contract(address=token, abi=self.erc_abi)
        allowance = token_contract.functions.allowance(signer, spender).call()

        if allowance < amount:
            max_amount = Web3.to_wei(2 ** 64 - 1, 'ether')

            transaction = token_contract.functions.approve(spender, max_amount).build_transaction({
                'from': signer,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(signer)
            })
            approve_tx = w3.eth.account.sign_transaction(transaction, self.private_key)
            tx = w3.eth.send_raw_transaction(approve_tx.rawTransaction)
            logger.success(f'Транзакция подтвержения {tx.hex()}')

    def get_token_balance(
            self,
            wallet: ChecksumAddress,
            token: ChecksumAddress,
            abi: list,
            w3: Web3,
            native: bool = False
    ) -> [int, str]:
        """Функция получения баланса токена"""

        token = w3.eth.contract(address=token, abi=abi)

        if native:
            name = self.get_token_name(token.functions.name().call())
            token_balance = w3.eth.get_balance(account=wallet)
        else:
            name = self.get_token_name(token.functions.name().call())
            token_balance = token.functions.balanceOf(wallet).call()

        return token_balance, name

    def get_matic_quantity(self, token: ChecksumAddress, name: str, w3: Web3, token_balance: int) -> Wei:
        """Функция перевода нативного токена сети отправителя в MATIC"""

        token_contract = w3.eth.contract(address=token, abi=self.erc_abi)
        decimals = token_contract.functions.decimals().call()
        token_balance = token_balance / (10 ** decimals)

        endpoint = f"/v3/ticker/price?symbols=[%22MATICUSDT%22,%22{name}USDT%22]"
        response = requests.get(self.binance_url + endpoint)
        data = response.json()
        matic_price, token_price = float(data[0]['price']), float(data[1]['price'])

        token_balance = (token_balance * (token_price / matic_price)) * const.COEFFICIENT

        return Web3.to_wei(token_balance, "ether")  # MATIC has same decimals as ether

    @staticmethod
    def create_swap_tx(
            wallet: ChecksumAddress,
            receive_network: str,
            native_info: dict,
            send_network: str,
            gas_price: int,
            amount: int,
            token: str,
            fee: int,
            w3: Web3,
            router,
    ) -> TxParams:

        amount_min = amount - (amount * const.SLIPPAGE) // 10

        txn = router.functions.swap(
            const.NETWORKS[receive_network],
            const.TOKEN_POOLS[send_network][token],
            const.TOKEN_POOLS[receive_network][token],
            wallet,
            amount,
            amount_min,
            native_info,
            wallet,
            "0x",
        ).build_transaction({
                'from': wallet,
                'value': fee,
                'gas': const.DEFAULT_GAS,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(wallet)
        })

        return txn

    @staticmethod
    def calculate_quote_layer_zero(network: str, native_info: dict, wallet: str, router) -> int:
        """Функция получение предполагаемой fee"""

        quote_data = router.functions.quoteLayerZeroFee(
            const.NETWORKS[network],
            1,
            wallet,
            '0x',
            (native_info)
        ).call()

        logger.info(f'Комиссия, полученная от моста: {quote_data[0]}')

        return quote_data[0]

    @staticmethod
    def connect_node(node_url: str) -> Web3:
        """Функция подключения к ноде"""

        return Web3(Web3.HTTPProvider(endpoint_uri=node_url))

    @staticmethod
    def get_token_name(string: str) -> str:
        """Функция получения названия токена"""

        plus_let = 'C' if 'coin' in string.lower() else ''

        for word in string.split(' '):

            if word.isupper():
                return word + plus_let
