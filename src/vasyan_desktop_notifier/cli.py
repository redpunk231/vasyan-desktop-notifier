import functools
import pathlib
import sys

import vasyan_core as core

SYSTEMD_SERVICE_NAME = 'vasyan-notifier.service'
SYSTEMD_SERVICE_TEMPLATE = '''
[Unit]
Description=Vasyan desktop notifier service
After=graphical-session.target

[Service]
Type=simple
ExecStart={path_app} run -c {path_config} -n {service_name}

[Install]
WantedBy=graphical-session.target
'''


class Cli(core.Cli):
    @functools.cached_property
    def _systemd(self) -> core.SystemdWrapper:
        return core.SystemdWrapper()

    def _get_systemd_unit_data(self, config: str, service_name: str | None) -> str:
        path_config = pathlib.Path(config)
        if not path_config.is_file():
            core.utils.terminate(f'Config file is not found: {config}')

        unit_data = SYSTEMD_SERVICE_TEMPLATE.format(
            path_app=sys.argv[0],
            path_config=path_config.absolute(),
            service_name=service_name or self._service_class.__service_name__
        )
        return unit_data.strip()

    def install(self, *, config: str, name: str | None = None) -> None:
        core.configure_logger()
        systemd_unit_data = self._get_systemd_unit_data(config, name)

        self._systemd.stop(SYSTEMD_SERVICE_NAME, missing_ok=True)
        self._systemd.create(SYSTEMD_SERVICE_NAME, systemd_unit_data)
        self._systemd.daemon_reload()
        self._systemd.enable(SYSTEMD_SERVICE_NAME)
        self._systemd.start(SYSTEMD_SERVICE_NAME)

        core.logger.success('Vasyan desktop notifier has been installed...')
