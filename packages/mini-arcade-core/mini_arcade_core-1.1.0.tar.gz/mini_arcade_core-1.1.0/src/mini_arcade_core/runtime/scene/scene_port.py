"""
Service interfaces for runtime components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from mini_arcade_core.scenes.registry import SceneRegistry

if TYPE_CHECKING:
    from mini_arcade_core.engine.game import Game
    from mini_arcade_core.scenes.scene import Scene
    from mini_arcade_core.sim.protocols import SimScene


@dataclass(frozen=True)
class ScenePolicy:
    """
    Controls how a scene behaves in the scene stack.

    blocks_update: if True, scenes below do not tick/update (pause modal)
    blocks_input:  if True, scenes below do not receive input
    is_opaque:     if True, scenes below are not rendered
    receives_input: if True, scene can receive input
    """

    blocks_update: bool = False
    blocks_input: bool = False
    is_opaque: bool = False
    receives_input: bool = True


@dataclass(frozen=True)
class SceneEntry:
    """
    An entry in the scene stack.

    :ivar scene_id (str): Identifier of the scene.
    :ivar scene (Scene): The scene instance.
    :ivar is_overlay (bool): Whether the scene is an overlay.
    :ivar policy (ScenePolicy): The scene's policy.
    """

    scene_id: str
    scene: SimScene
    is_overlay: bool
    policy: ScenePolicy


@dataclass
class StackItem:
    """
    An item in the scene stack.

    :ivar entry (SceneEntry): The scene entry.
    """

    entry: SceneEntry


class ScenePort:
    """Interface for scene management operations."""

    _registry: SceneRegistry
    _stack: List[StackItem]
    _game: Game

    @property
    def current_scene(self) -> "SimScene | None":
        """
        Get the currently active scene.

        :return: The active Scene instance, or None if no scene is active.
        :rtype: SimScene | None
        """

    @property
    def visible_stack(self) -> List["SimScene"]:
        """
        Return the list of scenes that should be drawn (base + overlays).
        We draw from the top-most non-overlay scene upward.

        :return: List of visible Scene instances.
        :rtype: List[SimScene]
        """

    def change(self, scene_id: str):
        """
        Change the current scene to the specified scene.

        :param scene_id: Identifier of the scene to switch to.
        :type scene_id: str
        """

    def push(self, scene_id: str, *, as_overlay: bool = False):
        """
        Push a new scene onto the scene stack.

        :param scene_id: Identifier of the scene to push.
        :type scene_id: str

        :param as_overlay: Whether to push the scene as an overlay.
        :type as_overlay: bool
        """

    def pop(self) -> "Scene | None":
        """
        Pop the current scene from the scene stack.

        :return: The popped Scene instance, or None if the stack was empty.
        :rtype: Scene | None
        """

    def clean(self):
        """
        Clean up all scenes from the scene stack.
        """

    def quit(self):
        """
        Quit the game
        """

    def visible_entries(self) -> list[SceneEntry]:
        """
        Render from bottom->top unless an opaque entry exists; if so,
            render only from that entry up.

        :return: List of SceneEntry instances to render.
        :rtype: list[SceneEntry]
        """

    def update_entries(self) -> list[SceneEntry]:
        """
        Tick/update scenes considering blocks_update.
        Typical: pause overlay blocks update below it.

        :return: List of SceneEntry instances to update.
        :rtype: list[SceneEntry]
        """

    def input_entry(self) -> SceneEntry | None:
        """
        Who gets input this frame. If top blocks_input, only it receives input.
        If not, top still gets input (v1 simple). Later you can allow fall-through.

        :return: The SceneEntry that receives input, or None if no scenes are active.
        :rtype: SceneEntry | None
        """

    def has_scene(self, scene_id: str) -> bool:
        """
        Check if a scene with the given ID exists in the stack.

        :param scene_id: Identifier of the scene to check.
        :type scene_id: str

        :return: True if the scene exists in the stack, False otherwise.
        :rtype: bool
        """

    def remove_scene(self, scene_id: str):
        """
        Remove a scene with the given ID from the stack.

        :param scene_id: Identifier of the scene to remove.
        :type scene_id: str
        """
