import fire

from .cli import Cli
from .service import DesktopNotifierService


def main() -> None:
    cli = Cli(DesktopNotifierService)
    fire.Fire(cli)
