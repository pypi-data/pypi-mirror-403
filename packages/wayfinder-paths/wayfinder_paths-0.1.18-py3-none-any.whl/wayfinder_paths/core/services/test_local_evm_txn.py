from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from wayfinder_paths.core.services.local_evm_txn import BASE_CHAIN_ID, LocalEvmTxn


class _FakeTxHash:
    def __init__(self, value: str):
        self._value = value

    def hex(self) -> str:
        return self._value


@pytest.mark.asyncio
async def test_base_defaults_to_two_confirmations():
    txn = LocalEvmTxn(config={})

    fake_web3 = MagicMock()
    fake_web3.eth = MagicMock()
    fake_web3.eth.send_raw_transaction = AsyncMock(return_value=_FakeTxHash("0x1"))
    fake_web3.eth.wait_for_transaction_receipt = AsyncMock(
        return_value={
            "status": 1,
            "blockNumber": 100,
            "transactionHash": "0x1",
            "gasUsed": 21_000,
            "logs": [],
        }
    )

    txn.get_web3 = MagicMock(return_value=fake_web3)
    txn._validate_transaction = MagicMock(side_effect=lambda tx: tx)
    txn._nonce_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_limit_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_price_transaction = AsyncMock(side_effect=lambda tx, _chain_id, _w3: tx)
    txn._sign_transaction = MagicMock(return_value=b"signed")
    txn._close_web3 = AsyncMock()
    txn._wait_for_confirmations = AsyncMock()

    ok, result = await txn.broadcast_transaction(
        {
            "chainId": BASE_CHAIN_ID,
            "from": "0x0000000000000000000000000000000000000001",
            "to": "0x0000000000000000000000000000000000000002",
            "value": 0,
        },
        wait_for_receipt=True,
        timeout=1,
    )

    assert ok is True
    txn._wait_for_confirmations.assert_awaited_once_with(fake_web3, 100, 2)
    assert result["confirmations"] == 2
    assert result["confirmed_block_number"] == 102


@pytest.mark.asyncio
async def test_non_base_defaults_to_zero_confirmations():
    txn = LocalEvmTxn(config={})

    fake_web3 = MagicMock()
    fake_web3.eth = MagicMock()
    fake_web3.eth.send_raw_transaction = AsyncMock(return_value=_FakeTxHash("0x1"))
    fake_web3.eth.wait_for_transaction_receipt = AsyncMock(
        return_value={
            "status": 1,
            "blockNumber": 100,
            "transactionHash": "0x1",
            "gasUsed": 21_000,
            "logs": [],
        }
    )

    txn.get_web3 = MagicMock(return_value=fake_web3)
    txn._validate_transaction = MagicMock(side_effect=lambda tx: tx)
    txn._nonce_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_limit_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_price_transaction = AsyncMock(side_effect=lambda tx, _chain_id, _w3: tx)
    txn._sign_transaction = MagicMock(return_value=b"signed")
    txn._close_web3 = AsyncMock()
    txn._wait_for_confirmations = AsyncMock()

    ok, result = await txn.broadcast_transaction(
        {
            "chainId": 1,
            "from": "0x0000000000000000000000000000000000000001",
            "to": "0x0000000000000000000000000000000000000002",
            "value": 0,
        },
        wait_for_receipt=True,
        timeout=1,
    )

    assert ok is True
    txn._wait_for_confirmations.assert_not_awaited()
    assert result["confirmations"] == 0
    assert result["confirmed_block_number"] == 100


@pytest.mark.asyncio
async def test_explicit_confirmations_override_defaults():
    txn = LocalEvmTxn(config={})

    fake_web3 = MagicMock()
    fake_web3.eth = MagicMock()
    fake_web3.eth.send_raw_transaction = AsyncMock(return_value=_FakeTxHash("0x1"))
    fake_web3.eth.wait_for_transaction_receipt = AsyncMock(
        return_value={
            "status": 1,
            "blockNumber": 100,
            "transactionHash": "0x1",
            "gasUsed": 21_000,
            "logs": [],
        }
    )

    txn.get_web3 = MagicMock(return_value=fake_web3)
    txn._validate_transaction = MagicMock(side_effect=lambda tx: tx)
    txn._nonce_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_limit_transaction = AsyncMock(side_effect=lambda tx, _w3: tx)
    txn._gas_price_transaction = AsyncMock(side_effect=lambda tx, _chain_id, _w3: tx)
    txn._sign_transaction = MagicMock(return_value=b"signed")
    txn._close_web3 = AsyncMock()
    txn._wait_for_confirmations = AsyncMock()

    ok, result = await txn.broadcast_transaction(
        {
            "chainId": BASE_CHAIN_ID,
            "from": "0x0000000000000000000000000000000000000001",
            "to": "0x0000000000000000000000000000000000000002",
            "value": 0,
        },
        wait_for_receipt=True,
        timeout=1,
        confirmations=0,
    )

    assert ok is True
    txn._wait_for_confirmations.assert_not_awaited()
    assert result["confirmations"] == 0
    assert result["confirmed_block_number"] == 100
