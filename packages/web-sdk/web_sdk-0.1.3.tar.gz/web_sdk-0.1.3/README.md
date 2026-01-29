[//]: # (DO NOT CHANGE THIS FILE MANUALLY. Use "make embed-readme" after changing README.template.md file)
<p align="center">
  <img src="docs/resources/brand.svg" width="100%" alt="Web SDK">
</p>
<p align="center">
    <em>WebSDK is a library for quickly and easily creating SDKs for integration with third-party APIs.</em>
</p>

<p align="center">

<a href="https://github.com/extralait-web/web-sdk/actions?query=event%3Apush+branch%3Amaster+workflow%3ACI" target="_blank">
    <img src="https://img.shields.io/github/actions/workflow/status/extralait-web/web-sdk/ci.yml?branch=master&logo=github&label=CI" alt="CI">
</a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/extralait-web/web-sdk" target="_blank">
    <img src="https://coverage-badge.samuelcolvin.workers.dev/extralait-web/web-sdk.svg" alt="Coverage">
</a>
<a href="https://pypi.python.org/pypi/web-sdk" target="_blank">
    <img src="https://img.shields.io/pypi/v/web-sdk.svg" alt="pypi">
</a>
<a href="https://pepy.tech/project/web-sdk" target="_blank">
    <img src="https://static.pepy.tech/badge/web-sdk/month" alt="downloads">
</a>
<a href="https://github.com/extralait-web/web-sdk" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/web-sdk.svg" alt="versions">
</a>
<a href="https://github.com/extralait-web/web-sdk" target="_blank">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/extralait-web/web-sdk/master/docs/badge/alfa.json" alt="Web SDK alfa">
</a>

</p>

[//]: # ([![llms.txt]&#40;https://img.shields.io/badge/llms.txt-green&#41;]&#40;https://docs.pydantic.dev/latest/llms.txt&#41;)

[//]: # ([![CondaForge]&#40;https://img.shields.io/conda/v/conda-forge/web-sdk.svg&#41;]&#40;https://anaconda.org/conda-forge/web-sdk&#41;)

# Installation

**REST installation**

Install using `pip install web-sdk[rest]` or `uv add web-sdk[rest]`

If you want to use `web_sdk.sdks.rest.XmlResponse`

Install using `pip install web-sdk[rest,xml]` or `uv add web-sdk[rest,xml]`

**SOAP installation**

Install using `pip install web-sdk[soap]` or `uv add web-sdk[soap]`

# Minimal example

Let's imagine that we have the following data schemas
```py
# docs/examples/home/minimal/dtos.py

from pydantic import BaseModel


# Response short data structure
class ShortData(BaseModel):
    pk: int = 1
    q: bool | None = None


# Response data structure
class Data(ShortData):
    nested: ShortData

```

To make the example simpler, we'll write the server part using [fastapi](https://fastapi.tiangolo.com/).
```py
# docs/examples/home/minimal/server.py

from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(root_path="/api/v1")


@app.get("/data/{pk}/info")
async def get_data_info(pk: int, q: bool | None = None) -> Data:
    """Return full data info."""
    return Data(pk=pk, q=q, nested=ShortData(pk=pk, q=q))


# route with short data return
@app.get("/data/{pk}/info/short")
async def get_short_data_info(pk: int, q: bool | None = None) -> ShortData:
    """Return short data info."""
    return ShortData(pk=pk, q=q)

```

To link with the routes declare in server code, you only need the following client code
```py
# docs/examples/home/minimal/client.py

from web_sdk.core.fields import APath
from web_sdk.enums import HTTPMethod
from web_sdk.sdks.rest import Client, ClientService, JsonResponse, Method, Service, Settings, get_res


# declare service for group of methods
class FooService(Service, path="data/{pk}/info"):
    get_data = Method[JsonResponse[Data]](method=HTTPMethod.GET)
    # declare method with return type and path (default method is GET)
    get_short_data = Method[JsonResponse[ShortData]](path="short")


# declare client service for group of real methods in client class
class FooClientService(ClientService):
    # declare method with certain signature pk is path part,
    # q is param (param type is default for GET method)
    @FooService.get_data
    def get_data(self, pk: APath[int], q: bool | None = None) -> JsonResponse[Data]: ...

    get_short_data = FooService.get_short_data.from_method(get_data)


# declare client class
class FooClient(Client):
    # set client services as annotation
    service: FooClientService

```

All you have to do next is init the client and call methods you need.
```py
# docs/examples/home/minimal/usage.py

# init client settings
settings = Settings(protocol="http", host="127.0.0.1", api_path="api/v1", port=8000)

# init client instance
client = FooClient(settings=settings)

# make get_data request
data_response = client.service.get_data(pk=1, q=True)
# extract data from response
data = get_res(data_response)
# Data(pk=1, q=True, nested=ShortData(pk=1, q=True))

# make get_short_data request
short_data_response = client.service.get_short_data(pk=1, q=True)
# extract data from response
short_data = get_res(short_data_response)
# ShortData(pk=1, q=True)

```

# Features
- [x] Annotation like request parts mapper
- [x] All requests methods support
- [x] Pydantic validation output and input data
- [x] File sending
- [x] Custom extra and context data during request
- [x] Errors logging
- [x] Custom client settings
- [x] Custom and token auth
- [x] Test mode settings support
- [x] Requests REST support
  - [x] Service declaration base request configuring
  - [x] Method declaration base request configuring
  - [x] Method call base request configuring
  - [x] Request call base request configuring
  - [ ] Path part mapping without field annotation
- [x] Requests SOAP support
  - [x] Custom transport for file sending
  - [ ] Service declaration base request configuring
  - [ ] Method declaration base request configuring
  - [ ] Method call base request configuring
  - [ ] Request call base request configuring
- [ ] HTTPX REST support
- [ ] HTTPX SOAP support
- [ ] MkDocs documentation

# Supported backends


## Sync backends


### Requests REST


Client and utils for declare the sync SDK based on [requests](https://github.com/psf/requests).

#### Declare custom or use default settings
```py
# docs/examples/home/sync/rest/settings.py

from pydantic_settings import SettingsConfigDict

from web_sdk.sdks.rest import Settings


class FooSettings(Settings):
    protocol: str = "https"
    """API protocol"""
    host: str = "example.com"
    """API host"""
    port: int | None = 8000
    """API port"""
    api_path: str = "/api/v1"
    """API path"""

    model_config = SettingsConfigDict(
        env_prefix="FOO_CLIENT_",
    )

```

#### Create responses schemas
```py
# docs/examples/home/sync/rest/schemas.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from web_sdk.sdks.rest import JsonResponse


class PaymentShortInfoDTO(BaseModel):
    id: str
    is_success: bool


class PaymentInfoDTO(PaymentShortInfoDTO):
    order_id: str
    payment_date: datetime
    payment_amount: Decimal


class OrderShortInfoDTO(BaseModel):
    id: str
    reference: str


class OrderInfoDTO(OrderShortInfoDTO):
    class _TargetDTO(BaseModel):
        id: str
        type: str
        price: Decimal

    # it is working with nested model
    target: _TargetDTO


GetPaymentResponse = JsonResponse[PaymentInfoDTO]
# it is working with list data
GetPaymentsResponse = JsonResponse[list[PaymentInfoDTO]]
MakePaymentResponse = JsonResponse[PaymentShortInfoDTO]
GetOrderResponse = JsonResponse[OrderInfoDTO]

```

#### Declare services with methods for using in client
```py
# docs/examples/home/sync/rest/methods.py

from web_sdk.enums import HTTPMethod
from web_sdk.sdks.rest import Method, Service

from . import schemas


class PaymentsService(
    Service,
    path="payments",
    description="Payments service",
):
    get = Method[schemas.GetPaymentResponse](
        path="{payment_id}",
        description="Get payment by id",
    )  # full path is "{settings.url}/payments/{payment_id}"

    make = Method[schemas.MakePaymentResponse](
        method=HTTPMethod.POST,
        path="make/{order_id}",
        description="Make payment for order",
    )  # full path is "{settings.url}/payments/make/{order_id}"


class OrdersService(
    Service,
    path="orders/{order_id}",
    description="Get order information by id",
):
    get = Method[schemas.GetOrderResponse](
        description="Get order information",
    )  # full path is "{settings.url}/orders/{order_id}"

    payments = Method[schemas.GetPaymentsResponse](
        path="payments",
        description="Get order payments",
    )  # full path is "{settings.url}/orders/{order_id}/payments"

```

#### Declare client and client services
```py
# docs/examples/home/sync/rest/client.py

from decimal import Decimal
from typing import Annotated

from typing_extensions import Unpack

from web_sdk.core.backends.requests.rest.kwargs import RestRequestsKwargsWithSettings
from web_sdk.core.fields import APath, ASetting, Body, Param, Path
from web_sdk.sdks.rest import Client, ClientService

from . import schemas
from .methods import OrdersService, PaymentsService
from .settings import FooSettings


class BaseFooClient(Client, base=True):
    """Here you can customize the client logic to suit your needs."""

    __default_settings_class__ = FooSettings


class FooClientService(ClientService[BaseFooClient], client=BaseFooClient):
    """This class need for isolate subclasses registering in user class."""


class PaymentsClientService(FooClientService):
    @PaymentsService.get
    def get(
        self,
        # ALike aliases (shortcut for Annotated[T, Field])
        payment_id: APath[int],
        # Unpack with TypedDict
        **kwargs: Unpack[RestRequestsKwargsWithSettings],
    ) -> schemas.GetPaymentResponse: ...

    @PaymentsService.make(timeout=5)
    def make(
        self,
        # Annotated[T, Field] like annotations
        order_id: Annotated[str, Path],
        # Other variant with Field call
        amount: Annotated[Decimal, Body(ge=Decimal("0"))],
        # Field as default value. You can also use a field without
        # specifying a default value, then the field will be
        # required (arg: bool = Param) or (arg: bool = Param()).
        immediately: bool | None = Param(None),  # type: ignore
        # Using settings to change Client.make_request behavior
        raise_exception: ASetting[bool | None] = None,
    ) -> schemas.MakePaymentResponse: ...


class OrdersClientService(FooClientService):
    @OrdersService.get
    def get(self, order_id: APath[int]) -> schemas.GetOrderResponse: ...

    @OrdersService.get
    def payments(
        self,
        order_id: APath[int],
        # For GET, DELETE, OPTION, HEAD methods default field is Param,
        # for POST, PATCH, PUT methods default field id Body
        success_only: bool = False,
    ) -> schemas.GetPaymentsResponse: ...


class FooClient(BaseFooClient):
    payments: PaymentsClientService
    orders: PaymentsClientService

```

#### Usage example
```py
# docs/examples/home/sync/rest/usage.py

from web_sdk.core.utils import make_client_factory
from web_sdk.sdks.rest import get_res

from .client import FooClient
from .settings import FooSettings

# You can just create client instance
# client = FooClient()

# But I recommend creating a client factory to cache instances
# based on the settings and logger hashes to avoid creating duplicate instances
client_factory = make_client_factory(FooClient, FooSettings)


# Create client
client = client_factory()

# Method response or error response if you use raise_exceptions=False
# or None if you use skip_for_tests
response = client.payments.get(
    payment_id=1,
    timeout=1,
    raise_exceptions=False,
)

result_or_none = get_res(response, required=False)
result = get_res(response)

```

### Requests SOAP

Client and utils for declare the sync SDK based on [requests](https://github.com/psf/requests), and [zeep](https://github.com/mvantellingen/python-zeep).


#### Declare custom or use default settings
```py
# docs/examples/home/sync/soap/settings.py

from pydantic_settings import SettingsConfigDict

from web_sdk.sdks.soap import Settings


class FooSettings(Settings):
    protocol: str = "https"
    """API protocol"""
    host: str = "example.com"
    """API host"""
    port: int | None = 8000
    """API port"""
    api_path: str = "/api/v1"
    """API path"""
    service_name: str | None = "service"
    """The name of wsdl service."""
    port_name: str | None = "port"
    """The name of wsdl port."""

    model_config = SettingsConfigDict(
        env_prefix="FOO_CLIENT_",
    )

```

#### Create responses schemas
```py
# docs/examples/home/sync/soap/schemas.py

from datetime import datetime
from decimal import Decimal
from typing import Generic

from pydantic import BaseModel

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases.soap import SoapFile
from web_sdk.sdks.soap import SoapResponse
from web_sdk.types import TData


class PaymentShortInfoDTO(PydanticModel):
    id: str
    is_success: bool


class PaymentInfoDTO(PydanticModel):
    order_id: str
    payment_date: datetime
    payment_amount: Decimal
    document: SoapFile


class PaymentsInfosDTO(PydanticModel):
    payments: list[PaymentInfoDTO]


class OrderShortInfoDTO(PydanticModel):
    id: str
    reference: str


class OrderInfoDTO(PydanticModel):
    class _TargetDTO(BaseModel):
        id: str
        type: str
        price: Decimal

    # it is working with nested model
    target: _TargetDTO


class FooResponse(SoapResponse, Generic[TData]):
    success: bool
    data: TData


GetPaymentResponse = FooResponse[PaymentInfoDTO]
GetPaymentsResponse = FooResponse[list[PaymentInfoDTO]]
MakePaymentResponse = FooResponse[PaymentShortInfoDTO]
GetOrderResponse = FooResponse[OrderInfoDTO]

```

#### Declare services with methods for using in client
```py
# docs/examples/home/sync/soap/methods.py

from web_sdk.sdks.soap import Method, Service

from . import schemas


class PaymentsService(
    Service,
    path="Payments",
    description="Payments service",
):
    get = Method[schemas.GetPaymentResponse](
        path="getPayment",
        description="Get payment by id",
    )  # method path is "Payments.getPayment"

    make = Method[schemas.MakePaymentResponse](
        path="makePayment",
        description="Make payment for order",
    )  # method path is "Payments.makePayment"


class OrdersService(
    Service,
    description="Get order information by id",
):
    get = Method[schemas.GetOrderResponse](
        description="Get order information",
    )  # method path is "get"

    payments = Method[schemas.GetPaymentsResponse](
        path="paymentsWithPath",
        description="Get order payments",
    )  # method path is "paymentsWithPath"

```

#### Declare client and client services
```py
# docs/examples/home/sync/soap/client.py

from decimal import Decimal
from typing import Annotated

from typing_extensions import Unpack

from web_sdk.core.backends.requests.soap.kwargs import SoapRequestsKwargsWithSettings
from web_sdk.core.fields import AFile, ASetting, Body
from web_sdk.sdks.soap import Client, ClientService, SoapFile

from . import schemas
from .methods import OrdersService, PaymentsService
from .settings import FooSettings


class BaseFooClient(Client, base=True):
    """Here you can customize the client logic to suit your needs."""

    __default_settings_class__ = FooSettings


class FooClientService(ClientService[BaseFooClient], client=BaseFooClient):
    """This class need for isolate subclasses registering in user class."""


# For soap client Body is base field type
class PaymentsClientService(FooClientService):
    @PaymentsService.get
    def get(
        self,
        # ALike aliases (shortcut for Annotated[T, Field])
        payment_id: int,
        # Unpack with TypedDict
        **kwargs: Unpack[SoapRequestsKwargsWithSettings],
    ) -> schemas.GetPaymentResponse: ...

    @PaymentsService.make
    def make(
        self,
        # Annotated[T, Field] like annotations
        order_id: Annotated[str, Body],
        # Other variant with Field call
        amount: Annotated[Decimal, Body(ge=Decimal("0"))],
        # Field as default value. You can also use a field without
        # specifying a default value, then the field will be
        # required (arg: bool = Body) or (arg: bool = Body()).
        immediately: bool | None = Body(None),  # type: ignore
        # Send single file with request
        payment_file: AFile[SoapFile | None] = None,
        # Send multiple files with request
        other_files: AFile[list[SoapFile] | None] = None,
        # Using settings to change Client.make_request behavior
        raise_exception: ASetting[bool | None] = None,
    ) -> schemas.MakePaymentResponse: ...


class OrdersClientService(FooClientService):
    @OrdersService.get
    def get(self, order_id: int) -> schemas.GetOrderResponse: ...

    @OrdersService.get
    def payments(
        self,
        order_id: int,
        success_only: bool = False,
    ) -> schemas.GetPaymentsResponse: ...


class FooClient(BaseFooClient):
    payments: PaymentsClientService
    orders: PaymentsClientService

```

#### Usage example
```py
# docs/examples/home/sync/soap/usage.py

from decimal import Decimal

from web_sdk.core.bases.soap import SoapFile
from web_sdk.core.utils import make_client_factory

from .client import FooClient
from .settings import FooSettings

# You can just create client instance
# client = FooClient()

# But I recommend creating a client factory to cache instances
# based on the settings and logger hashes to avoid creating duplicate instances
client_factory = make_client_factory(FooClient, FooSettings)


# Create client
client = client_factory()

# Method response or error response if you use raise_exceptions=False
# or None if you use skip_for_tests
response = client.payments.make(
    order_id="123",
    amount=Decimal("100"),
    payment_file=SoapFile(
        filename="payment.txt",
        content_type="text/plain",
        content=b"content",
    ),
    raise_exception=False,
)

```

## Async backends
Planned...


### Httpx REST


Planned...


### Httpx SOAP


Planned...
