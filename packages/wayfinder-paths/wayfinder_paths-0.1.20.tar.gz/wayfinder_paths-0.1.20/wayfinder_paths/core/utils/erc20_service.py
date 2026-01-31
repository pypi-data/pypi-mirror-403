from web3 import AsyncWeb3

from wayfinder_paths.core.constants.erc20_abi import ERC20_ABI
from wayfinder_paths.core.utils.web3 import web3_from_chain_id

NATIVE_CURRENCY_ADDRESSES: set = {
    "0x0000000000000000000000000000000000000000",
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    # TODO: This is not a proper SOL address, this short form is for LIFI only, fix this after fixing lifi
    "11111111111111111111111111111111",
    "0x0000000000000000000000000000000000001010",
}


async def get_token_balance(
    token_address: str, chain_id: int, wallet_address: str
) -> int:
    async with web3_from_chain_id(chain_id) as web3:
        checksum_wallet = AsyncWeb3.to_checksum_address(wallet_address)
        if not token_address or token_address.lower() in NATIVE_CURRENCY_ADDRESSES:
            balance = await web3.eth.get_balance(checksum_wallet)
            return int(balance)

        checksum_token = AsyncWeb3.to_checksum_address(token_address)
        contract = web3.eth.contract(address=checksum_token, abi=ERC20_ABI)
        balance = await contract.functions.balanceOf(checksum_wallet).call(
            block_identifier="pending"
        )
        return int(balance)


async def get_token_allowance(
    token_address: str, chain_id: int, owner_address: str, spender_address: str
):
    async with web3_from_chain_id(chain_id) as web3:
        contract = web3.eth.contract(
            address=web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        return await contract.functions.allowance(
            web3.to_checksum_address(owner_address),
            web3.to_checksum_address(spender_address),
        ).call(block_identifier="pending")


async def build_approve_transaction(
    from_address: str,
    chain_id: int,
    token_address: str,
    spender_address: str,
    amount: int,
) -> dict:
    async with web3_from_chain_id(chain_id) as web3:
        contract = web3.eth.contract(
            address=web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        data = contract.encode_abi(
            "approve",
            [
                web3.to_checksum_address(spender_address),
                amount,
            ],
        )
        return {
            "to": web3.to_checksum_address(token_address),
            "from": web3.to_checksum_address(from_address),
            "data": data,
            "chainId": chain_id,
        }


async def build_send_transaction(
    from_address: str,
    to_address: str,
    token_address: str | None,
    chain_id: int,
    amount: int,
) -> dict:
    async with web3_from_chain_id(chain_id) as web3:
        from_checksum = web3.to_checksum_address(from_address)
        to_checksum = web3.to_checksum_address(to_address)

        if not token_address or token_address.lower() in NATIVE_CURRENCY_ADDRESSES:
            return {
                "to": to_checksum,
                "from": from_checksum,
                "value": amount,
                "chainId": chain_id,
            }

        token_checksum = web3.to_checksum_address(token_address)
        contract = web3.eth.contract(address=token_checksum, abi=ERC20_ABI)
        data = contract.encode_abi("transfer", [to_checksum, amount])

        return {
            "to": token_checksum,
            "from": from_checksum,
            "data": data,
            "chainId": chain_id,
        }
