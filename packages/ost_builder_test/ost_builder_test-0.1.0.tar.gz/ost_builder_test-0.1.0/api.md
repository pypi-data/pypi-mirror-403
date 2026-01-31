# Health

Types:

```python
from ost_builder.types import HealthResponse
```

Methods:

- <code title="get /v1/health">client.health.<a href="./src/ost_builder/resources/health.py">check</a>() -> <a href="./src/ost_builder/types/health_response.py">HealthResponse</a></code>

# Exchange

Types:

```python
from ost_builder.types import (
    ExchangeCancelOrderResponse,
    ExchangeClosePositionResponse,
    ExchangeModifyOrderResponse,
    ExchangeOpenPositionResponse,
    ExchangeUpdateMarginResponse,
)
```

Methods:

- <code title="post /v1/exchange/cancel">client.exchange.<a href="./src/ost_builder/resources/exchange.py">cancel_order</a>(\*\*<a href="src/ost_builder/types/exchange_cancel_order_params.py">params</a>) -> <a href="./src/ost_builder/types/exchange_cancel_order_response.py">ExchangeCancelOrderResponse</a></code>
- <code title="post /v1/exchange/close">client.exchange.<a href="./src/ost_builder/resources/exchange.py">close_position</a>(\*\*<a href="src/ost_builder/types/exchange_close_position_params.py">params</a>) -> <a href="./src/ost_builder/types/exchange_close_position_response.py">ExchangeClosePositionResponse</a></code>
- <code title="get /v1/exchange/health">client.exchange.<a href="./src/ost_builder/resources/exchange.py">health_check</a>() -> <a href="./src/ost_builder/types/health_response.py">HealthResponse</a></code>
- <code title="post /v1/exchange/modify">client.exchange.<a href="./src/ost_builder/resources/exchange.py">modify_order</a>(\*\*<a href="src/ost_builder/types/exchange_modify_order_params.py">params</a>) -> <a href="./src/ost_builder/types/exchange_modify_order_response.py">ExchangeModifyOrderResponse</a></code>
- <code title="post /v1/exchange/order">client.exchange.<a href="./src/ost_builder/resources/exchange.py">open_position</a>(\*\*<a href="src/ost_builder/types/exchange_open_position_params.py">params</a>) -> <a href="./src/ost_builder/types/exchange_open_position_response.py">ExchangeOpenPositionResponse</a></code>
- <code title="post /v1/exchange/margin">client.exchange.<a href="./src/ost_builder/resources/exchange.py">update_margin</a>(\*\*<a href="src/ost_builder/types/exchange_update_margin_params.py">params</a>) -> <a href="./src/ost_builder/types/exchange_update_margin_response.py">ExchangeUpdateMarginResponse</a></code>
