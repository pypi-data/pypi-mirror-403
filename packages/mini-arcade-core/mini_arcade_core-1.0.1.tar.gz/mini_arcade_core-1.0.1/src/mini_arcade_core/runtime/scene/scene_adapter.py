"""
Module providing runtime adapters for window and scene management.
"""

from __future__ import annotations

from mini_arcade_core.runtime.context import RuntimeContext
from mini_arcade_core.runtime.scene.scene_port import (
    SceneEntry,
    ScenePolicy,
    ScenePort,
    StackItem,
)


class SceneAdapter(ScenePort):
    """
    Manages multiple scenes (not implemented).
    """

    def __init__(self, registry, game):
        self._registry = registry
        self._stack = []
        self._game = game

    @property
    def current_scene(self):
        return self._stack[-1].entry.scene if self._stack else None

    @property
    def visible_stack(self):
        return [e.scene for e in self.visible_entries()]

    def change(self, scene_id):
        self.clean()
        self.push(scene_id, as_overlay=False)

    def push(
        self,
        scene_id,
        *,
        as_overlay=False,
        policy=None,
    ):
        # default policy based on overlay vs base
        if policy is None:
            # base scenes: do not block anything by default
            policy = ScenePolicy()
        runtime_context = RuntimeContext.from_game(self._game)
        scene = self._registry.create(
            scene_id, runtime_context
        )  # or whatever your factory call is
        scene.on_enter()

        entry = SceneEntry(
            scene_id=scene_id,
            scene=scene,
            is_overlay=as_overlay,
            policy=policy,
        )
        self._stack.append(StackItem(entry=entry))

    def pop(self):
        if not self._stack:
            return
        item = self._stack.pop()
        item.entry.scene.on_exit()

    def clean(self):
        while self._stack:
            self.pop()

    def quit(self):
        self._game.quit()

    def visible_entries(self):
        entries = [i.entry for i in self._stack]
        # find highest opaque from top down; render starting there
        for idx in range(len(entries) - 1, -1, -1):
            if entries[idx].policy.is_opaque:
                return entries[idx:]
        return entries

    def update_entries(self):
        vis = self.visible_entries()
        if not vis:
            return []
        out = []
        for entry in reversed(vis):  # top->down
            out.append(entry)
            if entry.policy.blocks_update:
                break
        return list(reversed(out))  # bottom->top order

    def input_entry(self):
        vis = self.visible_entries()
        return vis[-1] if vis else None
