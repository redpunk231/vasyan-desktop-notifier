import uuid

import pydantic


def string_uuid() -> str:
    return str(uuid.uuid4())


class BrokerEvent(pydantic.BaseModel):
    tag: str
    data: dict[str, str]
    uuid: str = pydantic.Field(default_factory=string_uuid)


class EventAction(pydantic.BaseModel):
    name: str
    content: str
    content_type: str


class Event(pydantic.BaseModel):
    uuid: str
    title: str
    message: str
    level: str = 'NORMAL'
    icon: str | None = None
    sound: str | None = None
    actions: list[EventAction] = pydantic.Field(default_factory=list)

    def add_action(self, name: str, content: str, content_type: str) -> None:
        action = EventAction(name=name, content=content, content_type=content_type)
        self.actions.append(action)

    def get_action(self, name: str) -> EventAction | None:
        for action in self.actions:
            if action.name == name:
                return action
        return None
