"""
Entry point for the mini_arcade_core package.
Provides access to core classes and a convenience function to run a game.
"""

from __future__ import annotations

import traceback
from importlib.metadata import PackageNotFoundError, version
from typing import Callable, Type, Union

from mini_arcade_core.engine.game import Game, GameConfig, WindowConfig
from mini_arcade_core.scenes.registry import SceneRegistry
from mini_arcade_core.scenes.sim_scene import SimScene
from mini_arcade_core.utils import logger

SceneFactoryLike = Union[Type[SimScene], Callable[[Game], SimScene]]


# TODO: Improve exception handling and logging in run_game
# TODO: Consider reducing parameters by using a single config object
# TODO: Delegate responsibilities to Game class where appropriate
def run_game(
    scene: SceneFactoryLike | None = None,
    config: GameConfig | None = None,
    registry: SceneRegistry | None = None,
    initial_scene: str = "main",
):
    """
    Convenience helper to bootstrap and run a game with a single scene.

    Supports both:
        - run_game(SceneClass, cfg)            # legacy
        - run_game(config=cfg, initial_scene="main", registry=...)  # registry-based
        - run_game(cfg)                       # config-only

    :param scene: Optional SimScene factory/class to register
    :type scene: SceneFactoryLike | None

    :param initial_scene: The SimScene ID to start the game with.
    :type initial_scene: str

    :param config: Optional GameConfig to customize game settings.
    :type config: GameConfig | None

    :param registry: Optional SceneRegistry for scene management.
    :type registry: SceneRegistry | None

    :raises ValueError: If the provided config does not have a valid Backend.
    """
    try:
        # Handle run_game(cfg) where the first arg is actually a GameConfig
        if isinstance(scene, GameConfig) and config is None:
            config = scene
            scene = None

        cfg = config or GameConfig()
        if cfg.backend is None:
            raise ValueError(
                "GameConfig.backend must be set to a Backend instance"
            )

        # If user provided a SimScene factory/class, ensure it's registered
        if scene is not None:
            if registry is None:
                registry = SceneRegistry(_factories={})
            registry.register(
                initial_scene, scene
            )  # SimScene class is callable(game) -> SimScene

        game = Game(cfg, registry=registry)
        game.run(initial_scene)
    # Justification: We need to catch all exceptions while we improve error handling.
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.exception(f"Unhandled exception in game loop: {e}")
        logger.debug(traceback.format_exc())
    # pylint: enable=broad-exception-caught


PACKAGE_NAME = "mini-arcade-core"  # or whatever is in your pyproject.toml


def get_version() -> str:
    """
    Return the installed package version.

    This is a thin helper around importlib.metadata.version so games can do:

        from mini_arcade_core import get_version
        print(get_version())

    :return: The version string of the installed package.
    :rtype: str

    :raises PackageNotFoundError: If the package is not installed.
    """
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:  # if running from source / editable
        logger.warning(
            f"Package '{PACKAGE_NAME}' not found. Returning default version '0.0.0'."
        )
        return "0.0.0"


__all__ = [
    "Game",
    "GameConfig",
    "WindowConfig",
    "run_game",
]

__version__ = get_version()
