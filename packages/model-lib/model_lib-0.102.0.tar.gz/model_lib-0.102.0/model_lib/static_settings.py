import tempfile
from pathlib import Path
from typing import Self

import platformdirs
from pydantic import field_validator
from pydantic_settings import BaseSettings
from zero_3rdparty import humps


class StaticSettings(BaseSettings):
    STATIC_DIR: Path | None = None
    CACHE_DIR: Path | None = None
    SKIP_APP_NAME: bool = False

    @classmethod
    def app_name(cls) -> str:
        return humps.snake_case(cls.__qualname__.removesuffix("Settings"))

    @field_validator("STATIC_DIR", "CACHE_DIR", mode="before")
    @classmethod
    def _ensure_dir_exists(cls, v: Path | str | None) -> Path | None:
        if v is None:
            return None
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def for_testing(cls, tmp_path: Path | None = None, **kwargs) -> Self:
        tmp_path = tmp_path or Path(tempfile.gettempdir())
        static = tmp_path / "static"
        cache = tmp_path / "cache"
        static.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        return cls(STATIC_DIR=static, CACHE_DIR=cache, **kwargs)

    @classmethod
    def from_env(cls, **kwargs) -> Self:
        return cls(**kwargs)  # type: ignore

    @property
    def static_root(self) -> Path:
        if self.STATIC_DIR:
            base = self.STATIC_DIR
        else:
            base = Path(platformdirs.user_data_dir(self.app_name()))
        if self.SKIP_APP_NAME:
            base.mkdir(parents=True, exist_ok=True)
            return base
        app_dir = base / self.app_name()
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    @property
    def cache_root(self) -> Path:
        if self.CACHE_DIR:
            base = self.CACHE_DIR
        else:
            base = Path(platformdirs.user_cache_dir(self.app_name()))
        if self.SKIP_APP_NAME:
            base.mkdir(parents=True, exist_ok=True)
            return base
        app_dir = base / self.app_name()
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
