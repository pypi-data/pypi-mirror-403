"""
Command protocol for executing commands with a given context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Protocol, TypeVar

from mini_arcade_core.runtime.scene.scene_port import ScenePolicy

if TYPE_CHECKING:
    from mini_arcade_core.runtime.services import RuntimeServices

# Justification: Generic type for context
# pylint: disable=invalid-name
TContext = TypeVar("TContext")
# pylint: enable=invalid-name


@dataclass
class CommandContext:
    """
    Context for command execution.

    :ivar services (RuntimeServices): The runtime services.
    :ivar commands (CommandQueue | None): Optional command queue.
    :ivar settings (object | None): Optional settings object.
    :ivar world (object | None): The world object (can be any type).
    """

    services: RuntimeServices
    commands: Optional["CommandQueue"] = None
    settings: Optional[object] = None
    world: Optional[object] = None


class Command(Protocol):
    """
    A command is the only allowed "write path" from input/systems into:
    - scene operations (push/pop/change/quit)
    - capture
    - global game lifecycle
    - later: world mutations (if you pass a world reference)

    For now we keep it simple: commands only need RuntimeServices.
    """

    def execute(
        self,
        context: CommandContext,
    ):
        """
        Execute the command with the given world and runtime services.

        :param services: Runtime services for command execution.
        :type services: RuntimeServices

        :param commands: Optional command queue for command execution.
        :type commands: object | None

        :param settings: Optional settings object for command execution.
        :type settings: object | None

        :param world: The world object (can be any type).
        :type world: object | None
        """


@dataclass
class CommandQueue:
    """
    Queue for storing and executing commands.
    """

    _items: List[Command] = field(default_factory=list)

    def push(self, cmd: Command):
        """
        Push a command onto the queue.

        :param cmd: Command to be added to the queue.
        :type cmd: Command
        """
        self._items.append(cmd)

    def drain(self) -> List[Command]:
        """
        Drain and return all commands from the queue.

        :return: List of commands that were in the queue.
        :rtype: list[Command]
        """
        items = self._items
        self._items = []
        return items


@dataclass(frozen=True)
class QuitCommand(Command):
    """Quit the game."""

    def execute(
        self,
        context: CommandContext,
    ):
        context.services.scenes.quit()


@dataclass(frozen=True)
class ScreenshotCommand(Command):
    """
    Take a screenshot.

    :ivar label (str | None): Optional label for the screenshot file.
    """

    label: str | None = None

    def execute(
        self,
        context: CommandContext,
    ):
        context.services.capture.screenshot(label=self.label, mode="manual")


@dataclass(frozen=True)
class PushSceneCommand(Command):
    """
    Push a new scene onto the scene stack.

    :ivar scene_id (str): Identifier of the scene to push.
    :ivar as_overlay (bool): Whether to push the scene as an overlay.
    """

    scene_id: str
    as_overlay: bool = False

    def execute(
        self,
        context: CommandContext,
    ):
        context.services.scenes.push(self.scene_id, as_overlay=self.as_overlay)


@dataclass(frozen=True)
class PopSceneCommand(Command):
    """Pop the current scene from the scene stack."""

    def execute(
        self,
        context: CommandContext,
    ):
        context.services.scenes.pop()


@dataclass(frozen=True)
class ChangeSceneCommand(Command):
    """
    Change the current scene to the specified scene.

    :ivar scene_id (str): Identifier of the scene to switch to.
    """

    scene_id: str

    def execute(
        self,
        context: CommandContext,
    ):
        context.services.scenes.change(self.scene_id)


@dataclass(frozen=True)
class ToggleDebugOverlayCommand(Command):
    """
    Toggle the debug overlay scene.

    :cvar DEBUG_OVERLAY_ID: str: Identifier for the debug overlay scene.
    """

    DEBUG_OVERLAY_ID = "debug_overlay"

    def execute(self, context: CommandContext):
        scenes = context.services.scenes
        if scenes.has_scene(self.DEBUG_OVERLAY_ID):
            scenes.remove_scene(self.DEBUG_OVERLAY_ID)
            return

        scenes.push(
            self.DEBUG_OVERLAY_ID,
            as_overlay=True,
            policy=ScenePolicy(
                blocks_update=False,
                blocks_input=False,
                is_opaque=False,
                receives_input=False,
            ),
        )
