import typing

import pydantic
import vasyan_core as core

NotifyLevel = typing.Literal['LOW', 'NORMAL', 'CRITICAL']


class RuleAction(pydantic.BaseModel):
    name: str
    content: str
    content_type: str


class Rule(pydantic.BaseModel):
    tag: str
    title: str
    message: str
    icon: str | None = None
    sound: str | None = None
    level: NotifyLevel = 'NORMAL'
    actions: tuple[RuleAction, ...] = ()


class DesktopNotifierConfig(core.Config):
    rules: tuple[Rule, ...] = ()

    def get_rule(self, tag: str) -> Rule | None:
        for rule in self.rules:
            if rule.tag == tag:
                return rule
        return None
