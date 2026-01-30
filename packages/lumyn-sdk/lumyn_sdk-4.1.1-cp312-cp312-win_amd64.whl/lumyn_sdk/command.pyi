"""
Minimal type stub for lumyn_sdk.command
"""
from typing import Any, Optional
from enum import IntEnum


class MatrixTextScrollDirection(IntEnum):
    LEFT: int
    RIGHT: int


class MatrixTextFont(IntEnum):
    BUILTIN: int
    TINY_3X3: int
    PICOPIXEL: int
    TOM_THUMB: int
    ORG_01: int
    FREE_MONO_9: int
    FREE_MONO_BOLD_9: int
    FREE_SANS_9: int
    FREE_SANS_BOLD_9: int
    FREE_SERIF_9: int
    FREE_SERIF_BOLD_9: int
    FREE_MONO_12: int
    FREE_MONO_BOLD_12: int
    FREE_SANS_12: int
    FREE_SANS_BOLD_12: int
    FREE_SERIF_12: int
    FREE_SERIF_BOLD_12: int
    FREE_MONO_18: int
    FREE_MONO_BOLD_18: int
    FREE_SANS_18: int
    FREE_SANS_BOLD_18: int
    FREE_SERIF_18: int
    FREE_SERIF_BOLD_18: int
    FREE_MONO_24: int
    FREE_MONO_BOLD_24: int
    FREE_SANS_24: int
    FREE_SANS_BOLD_24: int
    FREE_SERIF_24: int
    FREE_SERIF_BOLD_24: int


class MatrixTextAlign(IntEnum):
    LEFT: int
    CENTER: int
    RIGHT: int


class MatrixTextFlags:
    smoothScroll: bool
    showBackground: bool
    pingPong: bool
    noScroll: bool
    reserved: int
    def __init__(self) -> None: ...


class AnimationColor:
    r: int
    g: int
    b: int
    def __init__(self, r: int = 0, g: int = 0, b: int = 0) -> None: ...


class CommandBuilder:
    @staticmethod
    def build(header: Any, body: bytes = b"") -> bytes: ...

    @staticmethod
    def buildSetAnimation(zone_id: int, animation_id: int, color: AnimationColor,
                          delay: int = 250, reversed: bool = False, one_shot: bool = False) -> bytes: ...

    @staticmethod
    def buildSetColor(zone_id: int, color: AnimationColor) -> bytes: ...

    @staticmethod
    def buildSetMatrixText(zone_id: int, text: str, color: AnimationColor,
                           direction: int = 0, delay: int = 500, one_shot: bool = False,
                           bg_color: AnimationColor = AnimationColor(), font: int = 0,
                           align: int = 0, flags: MatrixTextFlags = MatrixTextFlags(),
                           y_offset: int = 0) -> bytes: ...

    @staticmethod
    def buildSetMatrixTextGroup(group_id: int, text: str, color: AnimationColor,
                                direction: int = 0, delay: int = 500, one_shot: bool = False,
                                bg_color: AnimationColor = AnimationColor(), font: int = 0,
                                align: int = 0, flags: MatrixTextFlags = MatrixTextFlags(),
                                y_offset: int = 0) -> bytes: ...


# Exported names
MatrixTextScrollDirection = MatrixTextScrollDirection
MatrixTextFont = MatrixTextFont
MatrixTextAlign = MatrixTextAlign
MatrixTextFlags = MatrixTextFlags
AnimationColor = AnimationColor
CommandBuilder = CommandBuilder
