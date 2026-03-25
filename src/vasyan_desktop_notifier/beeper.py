from vasyan_core.utils import asynchronous, run_command


class Beeper:
    @classmethod
    def _check_do_not_distrub(cls) -> bool:
        result = run_command('dconf read /org/gnome/desktop/notifications/show-banners')
        return result.stdout != 'true'

    @classmethod
    @asynchronous
    def play(cls, path: str | None) -> None:
        if path is None:
            return
        if cls._check_do_not_distrub():
            return
        run_command(f'ffplay -v 0 -nodisp -autoexit -af "volume=2" {path}', wait=False)
