from pathlib import Path
from typing import Self, override

import dishka

from neva import Ok, Result, arch
from neva.config import ConfigRepository
from neva.testing import TestCase


class RequestService:
    """A service scoped to REQUEST."""

    def __init__(self) -> None:
        self.value = id(self)


class RequestScopedProvider(arch.ServiceProvider):
    """Registers a REQUEST-scoped service."""

    @override
    def register(self) -> Result[Self, str]:
        self.app.bind(
            RequestService,
            interface=RequestService,
            scope=dishka.Scope.REQUEST,
        )
        return Ok(self)


def _make_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    _ = (config_dir / "app.py").write_text(
        'config = {"name": "TestApp", "debug": True}'
    )
    _ = (config_dir / "providers.py").write_text(
        """
from tests.test_scope import RequestScopedProvider

config = {"providers": [RequestScopedProvider]}
"""
    )

    return config_dir


class TestScopeEntersChildScope(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_request_scoped_service_resolved_in_scope(self) -> None:
        with self.app.scope(dishka.Scope.REQUEST) as scoped:
            result = scoped.make(RequestService)

            assert result.is_ok

    async def test_request_scoped_service_not_resolved_at_app_scope(self) -> None:
        result = self.app.make(RequestService)

        assert result.is_err

    async def test_app_scoped_service_available_in_child_scope(self) -> None:
        with self.app.scope(dishka.Scope.REQUEST) as scoped:
            result = scoped.make(ConfigRepository)

            assert result.is_ok


class TestScopeRestoresContainer(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_container_restored_after_scope_exit(self) -> None:
        original_container = self.app.container

        with self.app.scope(dishka.Scope.REQUEST):
            assert self.app.container is not original_container

        assert self.app.container is original_container

    async def test_container_restored_after_exception(self) -> None:
        original_container = self.app.container

        try:
            with self.app.scope(dishka.Scope.REQUEST):
                msg = "intentional"
                raise RuntimeError(msg)
        except RuntimeError:
            pass

        assert self.app.container is original_container


class TestScopeInstanceLifetime(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_same_instance_within_scope(self) -> None:
        with self.app.scope(dishka.Scope.REQUEST) as scoped:
            first = scoped.make(RequestService).unwrap()
            second = scoped.make(RequestService).unwrap()

            assert first is second

    async def test_different_instances_across_scopes(self) -> None:
        with self.app.scope(dishka.Scope.REQUEST) as scoped:
            first = scoped.make(RequestService).unwrap()

        with self.app.scope(dishka.Scope.REQUEST) as scoped:
            second = scoped.make(RequestService).unwrap()

        assert first is not second


class TestScopeDefaultTarget(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_scope_without_argument_enters_next_non_skipped(self) -> None:
        with self.app.scope() as scoped:
            result = scoped.make(RequestService)

            assert result.is_ok


class TestNestedScopes(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_nested_scope_restores_to_parent_scope(self) -> None:
        with self.app.scope(dishka.Scope.REQUEST) as request_scoped:
            request_container = request_scoped.container

            with request_scoped.scope(dishka.Scope.ACTION) as action_scoped:
                assert action_scoped.container is not request_container

            assert request_scoped.container is request_container
