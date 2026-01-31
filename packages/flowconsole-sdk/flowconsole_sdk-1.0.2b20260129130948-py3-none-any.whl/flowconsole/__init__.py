r'''
# FlowConsole SDK

FlowConsole SDK contains the typed DSL for describing systems, components, and flows that the FlowConsole engine renders. It is built with `jsii`, so the same definitions are published to npm, PyPI, Maven, NuGet, and Go modules.

## Install

* Node.js: `npm install @flowconsole/sdk`
* Python (PyPI): `pip install flowconsole-sdk`
* .NET: `dotnet add package FlowConsole.Sdk`
* Maven:

  ```xml
  <dependency>
    <groupId>flowconsole</groupId>
    <artifactId>sdk</artifactId>
    <version>0.0.1</version>
  </dependency>
  ```
* Go: `go get github.com/slackmaster9999/flowconsole`

## Quick start (TypeScript)

When executed inside the FlowConsole runtime (as used by the playground/app), the SDK attaches flow helpers to your entities so you can describe interactions fluently:

```python
import { User, ReactApp, RestApi, Postgres } from '@flowconsole/sdk';

const user: User = { name: 'Customer', description: 'end user' };
const frontApp: ReactApp = { name: 'Customer Dashboard', description: 'React app' };
const restApi: RestApi = { name: 'Backend', description: 'Java REST API' };
const db: Postgres = { name: 'main_db', description: 'Database' };

user
  .sendsRequestTo(frontApp, 'opens in browser')
  .then(frontApp)
  .sendsRequestTo(restApi, 'GET /api/v1/dashboard/:id')
  .then(restApi)
  .sendsRequestTo(db, 'fetch dashboard data');
```

## Python package

* Package name: `flowconsole-sdk`, import module: `flowconsole`.
* Generated via `jsii-pacmak`; property names mirror the TypeScript definitions.
* The package ships the DSL types; use it alongside the FlowConsole engine that evaluates the objects you build.

## Building multi-language packages

1. Install dependencies from the repo root: `pnpm install`.
2. Build the TypeScript sources: `pnpm --filter @flowconsole/sdk build`.
3. Generate language-specific artifacts (including PyPI): `pnpm --filter @flowconsole/sdk package`. Artifacts are written to `src/sdk/dist/` (for JavaScript) and language subfolders such as `dist/python` (PyPI wheel/sdist). This README is used as the long description on PyPI.

## License

MIT — see `src/sdk/LICENSE`.
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *


class Component(metaclass=jsii.JSIIMeta, jsii_type="@flowconsole/sdk.Component"):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @jsii.member(jsii_name="executesRequest")
    def executes_request(self, action: builtins.str) -> "Component":
        '''
        :param action: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cec2922a429a3e995f1bd7e00f1c4982886fe27c74a186716dfda8a0a4859ceb)
            check_type(argname="argument action", value=action, expected_type=type_hints["action"])
        return typing.cast("Component", jsii.invoke(self, "executesRequest", [action]))

    @jsii.member(jsii_name="getDataFrom")
    def get_data_from(
        self,
        target: "Component",
        label: builtins.str,
        options: typing.Optional["ConnectionOptions"] = None,
    ) -> "Component":
        '''
        :param target: -
        :param label: -
        :param options: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__340ca80859888e3fe90caffc1e7152c43b9f613d4b8f2e89f09c8767ba078f7d)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument label", value=label, expected_type=type_hints["label"])
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
        return typing.cast("Component", jsii.invoke(self, "getDataFrom", [target, label, options]))

    @jsii.member(jsii_name="sendsRequest")
    def sends_request(
        self,
        target: "Component",
        label: builtins.str,
        options: typing.Optional["ConnectionOptions"] = None,
    ) -> "Component":
        '''
        :param target: -
        :param label: -
        :param options: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a68a63954d03341cc2740155c780213ace732bbcc96f5b8f7a0af3ea8bd194bd)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument label", value=label, expected_type=type_hints["label"])
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
        return typing.cast("Component", jsii.invoke(self, "sendsRequest", [target, label, options]))

    @jsii.member(jsii_name="then")
    def then(self, target: "Component") -> "Component":
        '''
        :param target: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7a0dbf81a61ee7973e09b5d771d3290b484611c6abe08b311e15a2411dc78562)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
        return typing.cast("Component", jsii.invoke(self, "then", [target]))

    @builtins.property
    @jsii.member(jsii_name="badge")
    def badge(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "badge"))

    @badge.setter
    def badge(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc92df991620977094919f5ab9400eab8984ad8e6bd401ca6e761d8152bbaa41)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "badge", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="belongsTo")
    def belongs_to(
        self,
    ) -> typing.Optional[typing.Union["Container", "ComputerSystem"]]:
        return typing.cast(typing.Optional[typing.Union["Container", "ComputerSystem"]], jsii.get(self, "belongsTo"))

    @belongs_to.setter
    def belongs_to(
        self,
        value: typing.Optional[typing.Union["Container", "ComputerSystem"]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__768220595b4b54e55d381895a5706ad8284de1d935604661cb61f0f8105eb1a6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "belongsTo", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "description"))

    @description.setter
    def description(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ea967272a0b37ecbcb677f94aca04dd4dc3dc50398cc6f2c9f0e4d6c717b619)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "description", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "id"))

    @id.setter
    def id(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a03a6d20b0f3ac2721cda80b13a16ca013b5582682e005a04611846c88c1e1b3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "name"))

    @name.setter
    def name(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2338cde0694af5219ac96660118954e78bc0b3f3046df7d4e3c8ffb3f6722755)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="root")
    def root(self) -> typing.Optional[typing.Union["Container", "ComputerSystem"]]:
        return typing.cast(typing.Optional[typing.Union["Container", "ComputerSystem"]], jsii.get(self, "root"))

    @root.setter
    def root(
        self,
        value: typing.Optional[typing.Union["Container", "ComputerSystem"]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eeaf1aed97424c75440c935cd95c7ba99a5f2db7d4deba6c381565193547a2cf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "root", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Optional[typing.List[builtins.str]]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__acc87460e322889b1ff620bbb1e22d09a3480d92d74cc0223cf900ba94066820)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tone")
    def tone(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tone"))

    @tone.setter
    def tone(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c72ace8ccff8e3e9efa1c40c824e53422b33b24b494d2ac8f1b7cd2e398609dc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tone", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@flowconsole/sdk.ComponentArgs",
    jsii_struct_bases=[],
    name_mapping={
        "badge": "badge",
        "belongs_to": "belongsTo",
        "description": "description",
        "id": "id",
        "name": "name",
        "tags": "tags",
        "tone": "tone",
    },
)
class ComponentArgs:
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba5f2ca6d9dd84fbd1ee5748a32bcb1b7445165b34f6c693c59b7447f8db0ed7)
            check_type(argname="argument badge", value=badge, expected_type=type_hints["badge"])
            check_type(argname="argument belongs_to", value=belongs_to, expected_type=type_hints["belongs_to"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument tone", value=tone, expected_type=type_hints["tone"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if badge is not None:
            self._values["badge"] = badge
        if belongs_to is not None:
            self._values["belongs_to"] = belongs_to
        if description is not None:
            self._values["description"] = description
        if id is not None:
            self._values["id"] = id
        if name is not None:
            self._values["name"] = name
        if tags is not None:
            self._values["tags"] = tags
        if tone is not None:
            self._values["tone"] = tone

    @builtins.property
    def badge(self) -> typing.Optional[builtins.str]:
        result = self._values.get("badge")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def belongs_to(
        self,
    ) -> typing.Optional[typing.Union["Container", "ComputerSystem"]]:
        result = self._values.get("belongs_to")
        return typing.cast(typing.Optional[typing.Union["Container", "ComputerSystem"]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tone(self) -> typing.Optional[builtins.str]:
        result = self._values.get("tone")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ComponentArgs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ComputerSystem(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.ComputerSystem",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="domain")
    def domain(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "domain"))

    @domain.setter
    def domain(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7cc704b3f287abfd34efc8fd02d057c0586fddfb8c0b75740677f0ecd4fc9c55)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "domain", value) # pyright: ignore[reportArgumentType]


class ConnectionOptions(
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.ConnectionOptions",
):
    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @builtins.property
    @jsii.member(jsii_name="detail")
    def detail(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "detail"))

    @detail.setter
    def detail(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb66fe21ccfc0e45d6af21bd70bf030292ab8fa321c0dd1d71baa95f519e8003)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "detail", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="icon")
    def icon(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "icon"))

    @icon.setter
    def icon(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40be1dc328aa4ce75ac28ab248df689dd4a974623b3b642b307f0d0a2ee3cc76)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "icon", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="kind")
    def kind(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "kind"))

    @kind.setter
    def kind(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cfc133dae7c91976e0c172a432c7117a8e4c71c06fec039d38718f77b6cb525c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "kind", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="muted")
    def muted(self) -> typing.Optional[builtins.bool]:
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "muted"))

    @muted.setter
    def muted(self, value: typing.Optional[builtins.bool]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7f8e91a41cc2c8695887dc34aa9675d84171f4aac7a4a6b7f7c67ae88c3a523e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "muted", value) # pyright: ignore[reportArgumentType]


class Container(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.Container",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="technology")
    def technology(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "technology"))

    @technology.setter
    def technology(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf36569a11a6674396877777a2f6b0ab4cd0f78f70f872f816637a744ba8b40a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "technology", value) # pyright: ignore[reportArgumentType]


class ExternalService(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.ExternalService",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="vendor")
    def vendor(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "vendor"))

    @vendor.setter
    def vendor(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7b9e08267687a6830bf14ed7c4b159838c02bfc696b5f5cb2a6c49655a41bfc2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "vendor", value) # pyright: ignore[reportArgumentType]


class KafkaTopic(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.KafkaTopic",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="partitionCount")
    def partition_count(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "partitionCount"))

    @partition_count.setter
    def partition_count(self, value: typing.Optional[jsii.Number]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48e9bdf12fd87a8ff4a443b705658e7f84ea6f39b2ac1733a07152a1910ea7b8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "partitionCount", value) # pyright: ignore[reportArgumentType]


class MessageQueue(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.MessageQueue",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="throughput")
    def throughput(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "throughput"))

    @throughput.setter
    def throughput(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d24be6a4d0347e11b675f1732530caa1f5a895617c3454886d132de2a0902e3e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "throughput", value) # pyright: ignore[reportArgumentType]


class Postgres(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.Postgres",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="schema")
    def schema(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "schema"))

    @schema.setter
    def schema(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13102c9b0e3a264c8ae337c79823e1c7e287cc5ff6742668d56d345b48078886)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schema", value) # pyright: ignore[reportArgumentType]


class ReactApp(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.ReactApp",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="framework")
    def framework(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "framework"))

    @framework.setter
    def framework(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__51f18039785f9906f6e026937c56f012dd766d71aa111d172372f0d543e44978)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "framework", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="url")
    def url(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "url"))

    @url.setter
    def url(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7fc309418483718a746dbf9085595d5753776731b7fa37e3d7984a646e8debb2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "url", value) # pyright: ignore[reportArgumentType]


class Redis(Component, metaclass=jsii.JSIIMeta, jsii_type="@flowconsole/sdk.Redis"):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "cluster"))

    @cluster.setter
    def cluster(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c585cb7b536ea6035b438b0f2619f0e2e2af0aeb4bbf397ea28ffb5fb7f5eb75)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "cluster", value) # pyright: ignore[reportArgumentType]


class RestApi(Component, metaclass=jsii.JSIIMeta, jsii_type="@flowconsole/sdk.RestApi"):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="endpoint")
    def endpoint(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpoint"))

    @endpoint.setter
    def endpoint(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17e12098041ebebc831f428ca1a2752b9fd4c0489e2c225bf4589eee8f0ea096)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpoint", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="method")
    def method(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "method"))

    @method.setter
    def method(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b4221570959355376ff598cd6e8de061ab8c7425275699485e31e3491d803504)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "method", value) # pyright: ignore[reportArgumentType]


class User(Component, metaclass=jsii.JSIIMeta, jsii_type="@flowconsole/sdk.User"):
    def __init__(
        self,
        *,
        role: typing.Optional[builtins.str] = None,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param role: 
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = UserArgs(
            role=role,
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "role"))

    @role.setter
    def role(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6026d013782cf30d07170e43d595c3b0a6cfccf0f746cae7850ba75863b30694)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "role", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@flowconsole/sdk.UserArgs",
    jsii_struct_bases=[ComponentArgs],
    name_mapping={
        "badge": "badge",
        "belongs_to": "belongsTo",
        "description": "description",
        "id": "id",
        "name": "name",
        "tags": "tags",
        "tone": "tone",
        "role": "role",
    },
)
class UserArgs(ComponentArgs):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
        role: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        :param role: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__541a78d6b3d916b3f08064e16df5ab02545de7f3d097afbcc7c272b638c0fb4f)
            check_type(argname="argument badge", value=badge, expected_type=type_hints["badge"])
            check_type(argname="argument belongs_to", value=belongs_to, expected_type=type_hints["belongs_to"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument tone", value=tone, expected_type=type_hints["tone"])
            check_type(argname="argument role", value=role, expected_type=type_hints["role"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if badge is not None:
            self._values["badge"] = badge
        if belongs_to is not None:
            self._values["belongs_to"] = belongs_to
        if description is not None:
            self._values["description"] = description
        if id is not None:
            self._values["id"] = id
        if name is not None:
            self._values["name"] = name
        if tags is not None:
            self._values["tags"] = tags
        if tone is not None:
            self._values["tone"] = tone
        if role is not None:
            self._values["role"] = role

    @builtins.property
    def badge(self) -> typing.Optional[builtins.str]:
        result = self._values.get("badge")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def belongs_to(
        self,
    ) -> typing.Optional[typing.Union["Container", "ComputerSystem"]]:
        result = self._values.get("belongs_to")
        return typing.cast(typing.Optional[typing.Union["Container", "ComputerSystem"]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tone(self) -> typing.Optional[builtins.str]:
        result = self._values.get("tone")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def role(self) -> typing.Optional[builtins.str]:
        result = self._values.get("role")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UserArgs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class BackgroundJob(
    Component,
    metaclass=jsii.JSIIMeta,
    jsii_type="@flowconsole/sdk.BackgroundJob",
):
    def __init__(
        self,
        *,
        badge: typing.Optional[builtins.str] = None,
        belongs_to: typing.Optional[typing.Union["Container", "ComputerSystem"]] = None,
        description: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Sequence[builtins.str]] = None,
        tone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param badge: 
        :param belongs_to: 
        :param description: 
        :param id: 
        :param name: 
        :param tags: 
        :param tone: 
        '''
        args = ComponentArgs(
            badge=badge,
            belongs_to=belongs_to,
            description=description,
            id=id,
            name=name,
            tags=tags,
            tone=tone,
        )

        jsii.create(self.__class__, self, [args])

    @builtins.property
    @jsii.member(jsii_name="schedule")
    def schedule(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "schedule"))

    @schedule.setter
    def schedule(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc7b290a37cda4b3c6af9537bbd9280fc016c9dbe8fd206177c0c77900277167)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schedule", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "BackgroundJob",
    "Component",
    "ComponentArgs",
    "ComputerSystem",
    "ConnectionOptions",
    "Container",
    "ExternalService",
    "KafkaTopic",
    "MessageQueue",
    "Postgres",
    "ReactApp",
    "Redis",
    "RestApi",
    "User",
    "UserArgs",
]

publication.publish()

def _typecheckingstub__cec2922a429a3e995f1bd7e00f1c4982886fe27c74a186716dfda8a0a4859ceb(
    action: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__340ca80859888e3fe90caffc1e7152c43b9f613d4b8f2e89f09c8767ba078f7d(
    target: Component,
    label: builtins.str,
    options: typing.Optional[ConnectionOptions] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a68a63954d03341cc2740155c780213ace732bbcc96f5b8f7a0af3ea8bd194bd(
    target: Component,
    label: builtins.str,
    options: typing.Optional[ConnectionOptions] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7a0dbf81a61ee7973e09b5d771d3290b484611c6abe08b311e15a2411dc78562(
    target: Component,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc92df991620977094919f5ab9400eab8984ad8e6bd401ca6e761d8152bbaa41(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__768220595b4b54e55d381895a5706ad8284de1d935604661cb61f0f8105eb1a6(
    value: typing.Optional[typing.Union[Container, ComputerSystem]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ea967272a0b37ecbcb677f94aca04dd4dc3dc50398cc6f2c9f0e4d6c717b619(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a03a6d20b0f3ac2721cda80b13a16ca013b5582682e005a04611846c88c1e1b3(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2338cde0694af5219ac96660118954e78bc0b3f3046df7d4e3c8ffb3f6722755(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eeaf1aed97424c75440c935cd95c7ba99a5f2db7d4deba6c381565193547a2cf(
    value: typing.Optional[typing.Union[Container, ComputerSystem]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__acc87460e322889b1ff620bbb1e22d09a3480d92d74cc0223cf900ba94066820(
    value: typing.Optional[typing.List[builtins.str]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c72ace8ccff8e3e9efa1c40c824e53422b33b24b494d2ac8f1b7cd2e398609dc(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ba5f2ca6d9dd84fbd1ee5748a32bcb1b7445165b34f6c693c59b7447f8db0ed7(
    *,
    badge: typing.Optional[builtins.str] = None,
    belongs_to: typing.Optional[typing.Union[Container, ComputerSystem]] = None,
    description: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Sequence[builtins.str]] = None,
    tone: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7cc704b3f287abfd34efc8fd02d057c0586fddfb8c0b75740677f0ecd4fc9c55(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb66fe21ccfc0e45d6af21bd70bf030292ab8fa321c0dd1d71baa95f519e8003(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40be1dc328aa4ce75ac28ab248df689dd4a974623b3b642b307f0d0a2ee3cc76(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cfc133dae7c91976e0c172a432c7117a8e4c71c06fec039d38718f77b6cb525c(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7f8e91a41cc2c8695887dc34aa9675d84171f4aac7a4a6b7f7c67ae88c3a523e(
    value: typing.Optional[builtins.bool],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bf36569a11a6674396877777a2f6b0ab4cd0f78f70f872f816637a744ba8b40a(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7b9e08267687a6830bf14ed7c4b159838c02bfc696b5f5cb2a6c49655a41bfc2(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48e9bdf12fd87a8ff4a443b705658e7f84ea6f39b2ac1733a07152a1910ea7b8(
    value: typing.Optional[jsii.Number],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d24be6a4d0347e11b675f1732530caa1f5a895617c3454886d132de2a0902e3e(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13102c9b0e3a264c8ae337c79823e1c7e287cc5ff6742668d56d345b48078886(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__51f18039785f9906f6e026937c56f012dd766d71aa111d172372f0d543e44978(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7fc309418483718a746dbf9085595d5753776731b7fa37e3d7984a646e8debb2(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c585cb7b536ea6035b438b0f2619f0e2e2af0aeb4bbf397ea28ffb5fb7f5eb75(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17e12098041ebebc831f428ca1a2752b9fd4c0489e2c225bf4589eee8f0ea096(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b4221570959355376ff598cd6e8de061ab8c7425275699485e31e3491d803504(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6026d013782cf30d07170e43d595c3b0a6cfccf0f746cae7850ba75863b30694(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__541a78d6b3d916b3f08064e16df5ab02545de7f3d097afbcc7c272b638c0fb4f(
    *,
    badge: typing.Optional[builtins.str] = None,
    belongs_to: typing.Optional[typing.Union[Container, ComputerSystem]] = None,
    description: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Sequence[builtins.str]] = None,
    tone: typing.Optional[builtins.str] = None,
    role: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc7b290a37cda4b3c6af9537bbd9280fc016c9dbe8fd206177c0c77900277167(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass
