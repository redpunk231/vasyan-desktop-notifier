import asyncio
import functools
import webbrowser

import desktop_notifier as dn
import vasyan_core as core

from .beeper import Beeper
from .config import DesktopNotifierConfig
from .models import BrokerEvent, Event

NOTIFY_CALLBACKS = {
    'URL': webbrowser.open,
}


class DesktopNotifierService(core.ProtoService[DesktopNotifierConfig]):
    events_subject_id = '*.notify'
    __service_name__ = 'desktop_notifier'
    __class_config__ = DesktopNotifierConfig

    def __post_init__(self) -> None:
        self._stop_event = asyncio.Event()
        self._beeper = Beeper()
        self._desktop_notifier = dn.DesktopNotifier()
        self._broker = core.brokers.broker_nats()

    def _validate_broker_event(self, data: bytes) -> BrokerEvent | None:
        try:
            event = BrokerEvent.model_validate_json(data)
            core.logger.info(f'Broker event: {event}')
            return event
        except Exception:
            core.logger.warning(f'Wrong broker event: {data}')
            return None

    def _validate_service_event(self, broker_event: BrokerEvent) -> Event | None:
        if (rule := self._config.get_rule(broker_event.tag)) is None:
            core.logger.info(f'No rule for event: {broker_event.uuid}')
            return None

        try:
            event = Event(
                uuid=broker_event.uuid,
                title=rule.title.format(**broker_event.data),
                message=rule.message.format(**broker_event.data),
                level=rule.level,
                icon=rule.icon,
                sound=rule.sound,
            )
            for action in rule.actions:
                event.add_action(
                    name=action.name,
                    content=action.content.format(**broker_event.data),
                    content_type=action.content_type
                )
            core.logger.info(f'Service event: {event}')
            return event
        except Exception as error:
            core.logger.warning(f'Unable to validate service event: {error}')
            return None

    async def _inbox_callback(self, message: core.protocols.BrokerMessage) -> None:
        core.logger.debug(f'Received broker message: {message}')
        if not (broker_event := self._validate_broker_event(message.data)):
            return
        if not (service_event := self._validate_service_event(broker_event)):
            return
        await self._process_event(service_event)

    async def _process_event(self, event: Event) -> None:
        core.logger.info(f'Process service event: {event.uuid}')
        await self._desktop_notifier.send(
            title=event.title,
            message=event.message,
            urgency=dn.Urgency(event.level.lower()),
            icon=dn.Icon(name=event.icon),
            on_clicked=functools.partial(self._notify_callback, 'click', event),
            on_dismissed=functools.partial(self._notify_callback, 'cancel', event),
        )
        await self._beeper.play(event.sound)

    def _notify_callback(self, action: str, event: Event) -> None:
        core.logger.debug(f'Service event callback [{action} | {event.uuid}]')
        if (event_action := event.get_action(action)) is None:
            return

        callback = NOTIFY_CALLBACKS.get(event_action.content_type, lambda _: None)
        callback(event_action.content)

    async def _prepare_service(self) -> None:
        await self._broker.connect()
        await self._broker.subscribe(
            subject=self.events_subject_id,
            callback=self._inbox_callback
        )

    async def _run_service(self) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(0.1)

    def _stop_service(self) -> None:
        self._stop_event.set()

    async def _cleanup_service(self) -> None:
        await self._broker.disconnect()
