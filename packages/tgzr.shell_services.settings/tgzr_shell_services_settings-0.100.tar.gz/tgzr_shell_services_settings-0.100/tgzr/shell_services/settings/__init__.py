from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Awaitable, Any

import logging

from tgzr.shell.settings import SettingsClientPlugin, SettingsModelType
from tgzr.contextual_settings.stores.jetstream_store import (
    JetStreamStoreClient,
    ClientBroker,
)

if TYPE_CHECKING:
    from tgzr.shell.session import Session
    from tgzr.shell.services import AsyncBroker

logger = logging.getLogger(__name__)


class _TgzrSessionSettingsBroker(ClientBroker):
    """
    This is used to connect the JetStreamStore to the session's broker.

    See `tgzr.contextual_settings.stores.jetstream_store.ClientBroker()`
    """

    def __init__(self, stream_name: str, subject_prefix: str):
        super().__init__(stream_name, subject_prefix)
        self._session: Session = None  # type: ignore

        self._service_name = subject_prefix
        self._cmd_subject_prefix = f"{subject_prefix}.$CMD."
        self._request_subject_prefix = f"{subject_prefix}.$QUERY."
        self._touch_event_prefix = f"{subject_prefix}.$EVENT."

    async def connect(self, session: Session) -> None:
        self._session = session
        self._touch_subscription = await session.subscribe(
            self._touch_event_prefix + ">", self._on_touch_event
        )

    async def disconnect(self) -> None:
        if self._touch_subscription is not None:
            await self._session.unsubscribe(self._touch_subscription)

    async def send_cmd(self, cmd_name, **cmd_kwargs) -> None:
        await self._session.execute_service_cmd(
            self._service_name, cmd_name, **cmd_kwargs
        )

    async def send_query(self, query_name: str, **query_kwargs) -> Any:
        data = await self._session.execute_service_query(
            self._service_name, query_name, **query_kwargs
        )
        return data


async def set_test_values(settings: SettingsClient):
    await settings.set_context_info(
        "system",
        icon="api",
        color="#008888",
        description="##### **Fake context** \n\n##### 🫣 just for testing...",
    )
    await settings.set("system", "system_key", "system_value")
    await settings.set("system", "test_key", "system_value")
    await settings.set("system", "test_list_key", ["system_value"])

    await settings.set_context_info(
        "admin", icon="admin_panel_settings", color="#880088"
    )
    await settings.set("admin", "admin_key", "admin_value")
    await settings.set("admin", "test_key", "admin_value")
    await settings.add("admin", "test_list_key", ["admin_value1", "admin_value2"])

    await settings.set_context_info("user", icon="person", color="#888800")
    await settings.set("user", "user_key", "user_value")
    await settings.set("user", "test_key", "user_value")
    await settings.remove("admin", "test_list_key", "system_value")


class SettingsClient(SettingsClientPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store: JetStreamStoreClient = None  # type: ignore

    async def connect(self, session: Session) -> None:
        await super().connect(session)

        stream_name = f"{session.config.stream_name_prefix}_settings"
        subject_prefix = f"{session.config.subject_prefix}.settings"

        logger.info("+ SettingsClient Connecting:")
        logger.info(f"      Stream Name: {stream_name}")
        logger.info(f"   Subject_prefix: {subject_prefix}")
        session_broker = _TgzrSessionSettingsBroker(
            stream_name=stream_name, subject_prefix=subject_prefix
        )
        self._store = JetStreamStoreClient(session_broker)
        await self._store.connect(self.session)

        if 0:
            await set_test_values(self)

    async def disconnect(self):
        if self._store is not None:
            await self._store.disconnect()

    @property
    def _(self) -> JetStreamStoreClient:
        if self._store is None:
            raise RuntimeError(
                "SettingsClient not connected. Please call connect() first!"
            )
        return self._store

    #
    # ---
    #

    async def watch_changes(
        self, callback: Callable[[AsyncBroker.Event], Awaitable[None]]
    ):
        self._store.add_on_touched(callback)

    #
    # ---
    #

    async def get_context_names(self) -> tuple[str, ...]:
        return await self._.get_context_names()

    async def set_context_info(self, context_name: str, **info: Any) -> None:
        return await self._.set_context_info(context_name, **info)

    async def get_context_info(self, context_name: str) -> dict[str, Any]:
        return await self._.get_context_info(context_name)

    def expand_context_name(self, context_name: str) -> list[str]:
        return self._.expand_context_name(context_name)

    #
    # ---
    #

    async def get_context_flat(
        self,
        context: list[str],
        path: str | None = None,
        with_history: bool = False,
    ) -> dict[str, Any]:
        return await self._.get_context_flat(context, path, with_history)

    async def get_context_dict(
        self, context: list[str], path: str | None = None, with_history: bool = False
    ) -> dict[str, Any]:
        return await self._.get_context_dict(context, path, with_history)

    async def get_context(
        self,
        context: list[str],
        model_type: type[SettingsModelType],
        path: str | None = None,
    ) -> SettingsModelType:
        return await self._.get_context(context, model_type, path)

    #
    # ---
    #

    async def update_context_flat(
        self, context_name: str, flat_dict: dict[str, Any], path: str | None = None
    ) -> None:
        await self._.update_context_flat(
            context_name=context_name, flat_dict=flat_dict, path=path
        )

    async def update_context_dict(
        self,
        context_name: str,
        deep_dict: dict[str, Any | dict[str, Any]],
        path: str | None = None,
    ) -> None:
        await self._.update_context_dict(
            context_name=context_name, deep_dict=deep_dict, path=path
        )

    async def update_context(
        self,
        context_name: str,
        model: SettingsModelType,
        path: str | None = None,
        exclude_defaults: bool = True,
    ):
        await self._.update_context(
            context_name=context_name,
            model=model,
            path=path,
            exclude_defaults=exclude_defaults,
        )

    #
    # ---
    #
    async def _send_cmd(self, cmd_name: str, **kwargs: str) -> None:
        # TODO: get ride of this, but tgzr.nice.data_element.contextual_settings_view still uses it :/
        await self._._send_cmd(cmd_name=cmd_name, **kwargs)

    async def set(self, context_name: str, name: str, value: Any) -> None:
        await self._.set(context_name=context_name, name=name, value=value)

    async def toggle(self, context_name: str, name: str) -> None:
        await self._.toggle(context_name=context_name, name=name)

    async def add(self, context_name: str, name: str, value: Any) -> None:
        await self._.add(context_name=context_name, name=name, value=value)

    async def sub(self, context_name: str, name: str, value: Any) -> None:
        await self._.sub(context_name=context_name, name=name, value=value)

    async def set_item(
        self, context_name: str, name: str, index: int, item_value: Any
    ) -> None:
        await self._.set_item(
            context_name=context_name, name=name, index=index, item_value=item_value
        )

    async def del_item(self, context_name: str, name: str, index: int) -> None:
        await self._.del_item(context_name=context_name, name=name, index=index)

    async def remove(self, context_name: str, name: str, item: str) -> None:
        await self._.remove(context_name=context_name, name=name, item=item)

    async def append(self, context_name: str, name: str, value: Any) -> None:
        await self._.append(context_name=context_name, name=name, value=value)

    async def env_override(
        self, context_name: str, name: str, envvar_name: str
    ) -> None:
        await self._.env_override(
            context_name=context_name, name=name, envvar_name=envvar_name
        )

    async def pop(self, context_name: str, name: str, index: int | slice) -> None:
        await self._.pop(context_name=context_name, name=name, index=index)

    async def remove_slice(
        self,
        context_name: str,
        name: str,
        start: int,
        stop: int,
        step: int | None = None,
    ) -> None:
        await self._.remove_slice(
            context_name=context_name, name=name, start=start, stop=stop, step=step
        )

    async def call(
        self,
        context_name: str,
        name: str,
        method_name: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> None:
        await self._.call(
            context_name=context_name,
            name=name,
            method_name=method_name,
            args=args,
            kwargs=kwargs,
        )


async def test():
    from tgzr.shell.session import Session

    session = Session()
    print(session.settings)
    await session.connect()
    print("Context names:", await session.settings.get_context_names())
    # if 1:
    #     print(await session.settings.set_context_info("test_context", color="red"))
    print("Context info:", await session.settings.get_context_info("test_context"))

    await session.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
