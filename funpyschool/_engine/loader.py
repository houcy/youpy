# -*- encoding: utf-8 -*-
"""
"""


from pathlib import Path
from importlib import import_module
import operator
from collections.abc import Callable

from .media import Image
from .events import try_make_event
from .events import EVENT_FUNC_PREFIX
from .sprite import Sprite


def _add_item_to_dict(d, obj):
    assert " " not in obj.name
    d[obj.name] = obj

class Loader:

    def __init__(self, progress=None):
        self.progress = progress or DummyProgress()

    def load(self, engine):
        self._load_backdrops(engine)
        self._load_sprites(engine)

    def _load_backdrops(self, engine):
        for i, path in enumerate(iter_images_set(engine.project.stage_dir)):
            _add_item_to_dict(engine.scene.backdrops, Image(path))
            self.progress.in_section("backdrops", i, path)
        load_events_to(engine.events,
                       import_module(engine.project.stage_module_path))
        self.progress.end_section()

    def _load_sprites(self, engine):
        for i, path in enumerate(engine.project.iter_sprite_dirs()):
            sprite = Sprite(path)
            load_sprite_images(sprite)
            load_events_to(
                engine.events,
                import_module(engine.project.sprite_module_path(sprite.name)),
                sprite=sprite)
            _add_item_to_dict(engine.sprites, sprite)
            self.progress.in_section("sprites", i, path)
        self.progress.end_section()

class DummyProgress:

    def in_section(self, name, index, path):
        pass

    def end_section(self):
        pass

def iter_images_set(path):
    path = Path(path)
    assert path.is_dir()
    for p in path.iterdir():
        if p.suffix in (".png", ".jpg"):
            yield p

def load_images_set(path):
    l = [Image(p) for p in iter_images_set(path)]
    l.sort(key=operator.attrgetter("index"))
    return l

def load_sprite_images(sprite):
    sprite.images = load_images_set(sprite.path)
    assert len(sprite.images) > 0
    sprite._index = 0
    sprite.rect = sprite.current_image.rect

def load_events_to(eventset, mod, sprite=None):
    """
    Arguments:
      sprite: might be None for the stage.
    """
    for attr in dir(mod):
        if attr.startswith(EVENT_FUNC_PREFIX):
            obj = getattr(mod, attr)
            if isinstance(obj, Callable) and hasattr(obj, "__name__"):
                event = try_make_event(obj, sprite=sprite)
                if event is None:
                    raise RuntimeError(f"invalid event name: '{attr}'")
                eventset.add(event)
