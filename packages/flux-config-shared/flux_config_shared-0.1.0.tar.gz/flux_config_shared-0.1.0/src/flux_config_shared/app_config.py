"""Application configuration for TUI and other clients."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import ClassVar

import aiofiles
import yaml
from textual.theme import BUILTIN_THEMES


@dataclass
class AppConfig:
    config_path: ClassVar[str] = "/mnt/root/config/app_config.yaml"
    theme: str = "flexoki"
    poweroff_screen: int = 0
    screen_resolutions: list[str] = field(default_factory=list)
    selected_resolution: str | None = None

    asdict = asdict

    @classmethod
    def from_file(cls) -> AppConfig:
        try:
            with open(cls.config_path) as f:
                data = f.read()
        except FileNotFoundError:
            instance = cls()
            instance.persist_sync()
            return instance

        conf: dict = yaml.safe_load(data)

        filtered = {field.name: conf.get(field.name) for field in fields(cls) if field.name in conf}

        return cls(**filtered)

    async def update(
        self,
        *,
        theme: str | None = None,
        poweroff_screen: int | None = None,
        resolutions: list[str] | None = None,
        selected_resolution: str | None = None,
    ) -> None:
        needs_persist = False

        if theme and theme in BUILTIN_THEMES and self.theme != theme:
            self.theme = theme
            needs_persist = True

        if poweroff_screen is not None and self.poweroff_screen != poweroff_screen:
            self.poweroff_screen = poweroff_screen
            needs_persist = True

        if resolutions:
            self.screen_resolutions = resolutions
            needs_persist = True

        if selected_resolution and self.selected_resolution != selected_resolution:
            self.selected_resolution = selected_resolution
            needs_persist = True

        if needs_persist:
            await self.persist()

    def update_sync(
        self,
        *,
        theme: str | None = None,
        poweroff_screen: int | None = None,
        resolutions: list[str] | None = None,
    ) -> None:
        needs_persist = False

        if theme and theme in BUILTIN_THEMES and self.theme != theme:
            self.theme = theme
            needs_persist = True

        if poweroff_screen is not None and self.poweroff_screen != poweroff_screen:
            self.poweroff_screen = poweroff_screen
            needs_persist = True

        if resolutions:
            self.screen_resolutions = resolutions
            needs_persist = True

        if needs_persist:
            self.persist_sync()

    async def persist(self) -> None:
        conf = yaml.dump(self.asdict())

        async with aiofiles.open(AppConfig.config_path, "w") as f:
            await f.write(conf)

    def persist_sync(self) -> None:
        conf = yaml.dump(self.asdict())

        with open(AppConfig.config_path, "w") as f:
            f.write(conf)
