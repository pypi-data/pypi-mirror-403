# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from ost_builder import OstBuilder, AsyncOstBuilder
from tests.utils import assert_matches_type
from ost_builder.types import (
    HealthResponse,
    ExchangeCancelOrderResponse,
    ExchangeModifyOrderResponse,
    ExchangeOpenPositionResponse,
    ExchangeUpdateMarginResponse,
    ExchangeClosePositionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExchange:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel_order(self, client: OstBuilder) -> None:
        exchange = client.exchange.cancel_order(
            cancels=[{"t": "limit"}],
        )
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel_order_with_all_params(self, client: OstBuilder) -> None:
        exchange = client.exchange.cancel_order(
            cancels=[
                {
                    "t": "limit",
                    "a": 0,
                    "i": 1,
                    "o": 0,
                }
            ],
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel_order(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.cancel_order(
            cancels=[{"t": "limit"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel_order(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.cancel_order(
            cancels=[{"t": "limit"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_close_position(self, client: OstBuilder) -> None:
        exchange = client.exchange.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        )
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_close_position_with_all_params(self, client: OstBuilder) -> None:
        exchange = client.exchange.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
            sp=0.5,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_close_position(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_close_position(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_health_check(self, client: OstBuilder) -> None:
        exchange = client.exchange.health_check()
        assert_matches_type(HealthResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_health_check(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.health_check()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(HealthResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_health_check(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.health_check() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(HealthResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_order(self, client: OstBuilder) -> None:
        exchange = client.exchange.modify_order(
            a=0,
            i=1,
        )
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_modify_order_with_all_params(self, client: OstBuilder) -> None:
        exchange = client.exchange.modify_order(
            a=0,
            i=1,
            p="41000.00",
            sl="38000.00",
            tp="46000.00",
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_modify_order(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.modify_order(
            a=0,
            i=1,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_modify_order(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.modify_order(
            a=0,
            i=1,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_open_position(self, client: OstBuilder) -> None:
        exchange = client.exchange.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        )
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_open_position_with_all_params(self, client: OstBuilder) -> None:
        exchange = client.exchange.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                    "sl": "40000.00",
                    "tp": "45000.00",
                }
            ],
            bd={
                "b": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
                "f": 0.1,
            },
            sp=0.5,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_open_position(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_open_position(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_margin(self, client: OstBuilder) -> None:
        exchange = client.exchange.update_margin(
            a=0,
            amount="50.00",
            i=0,
        )
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_margin_with_all_params(self, client: OstBuilder) -> None:
        exchange = client.exchange.update_margin(
            a=0,
            amount="50.00",
            i=0,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_margin(self, client: OstBuilder) -> None:
        response = client.exchange.with_raw_response.update_margin(
            a=0,
            amount="50.00",
            i=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = response.parse()
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_margin(self, client: OstBuilder) -> None:
        with client.exchange.with_streaming_response.update_margin(
            a=0,
            amount="50.00",
            i=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = response.parse()
            assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncExchange:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel_order(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.cancel_order(
            cancels=[{"t": "limit"}],
        )
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel_order_with_all_params(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.cancel_order(
            cancels=[
                {
                    "t": "limit",
                    "a": 0,
                    "i": 1,
                    "o": 0,
                }
            ],
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel_order(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.cancel_order(
            cancels=[{"t": "limit"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel_order(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.cancel_order(
            cancels=[{"t": "limit"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(ExchangeCancelOrderResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_close_position(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        )
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_close_position_with_all_params(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
            sp=0.5,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_close_position(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_close_position(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.close_position(
            closes=[
                {
                    "a": 0,
                    "p": "43000.00",
                    "r": 100,
                    "t": 0,
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(ExchangeClosePositionResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_health_check(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.health_check()
        assert_matches_type(HealthResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_health_check(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.health_check()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(HealthResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_health_check(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.health_check() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(HealthResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_order(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.modify_order(
            a=0,
            i=1,
        )
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_modify_order_with_all_params(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.modify_order(
            a=0,
            i=1,
            p="41000.00",
            sl="38000.00",
            tp="46000.00",
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_modify_order(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.modify_order(
            a=0,
            i=1,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_modify_order(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.modify_order(
            a=0,
            i=1,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(ExchangeModifyOrderResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_open_position(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        )
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_open_position_with_all_params(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                    "sl": "40000.00",
                    "tp": "45000.00",
                }
            ],
            bd={
                "b": "0x742d35Cc6634C0532925a3b844Bc9e7595f5bE21",
                "f": 0.1,
            },
            sp=0.5,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_open_position(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_open_position(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.open_position(
            orders=[
                {
                    "a": 0,
                    "b": True,
                    "l": "10",
                    "p": "42500.00",
                    "s": "100",
                    "t": "market",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(ExchangeOpenPositionResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_margin(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.update_margin(
            a=0,
            amount="50.00",
            i=0,
        )
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_margin_with_all_params(self, async_client: AsyncOstBuilder) -> None:
        exchange = await async_client.exchange.update_margin(
            a=0,
            amount="50.00",
            i=0,
            x_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_margin(self, async_client: AsyncOstBuilder) -> None:
        response = await async_client.exchange.with_raw_response.update_margin(
            a=0,
            amount="50.00",
            i=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        exchange = await response.parse()
        assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_margin(self, async_client: AsyncOstBuilder) -> None:
        async with async_client.exchange.with_streaming_response.update_margin(
            a=0,
            amount="50.00",
            i=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            exchange = await response.parse()
            assert_matches_type(ExchangeUpdateMarginResponse, exchange, path=["response"])

        assert cast(Any, response.is_closed) is True
