"""
Minimal type stub for lumyn_sdk.connectorx
"""
from typing import Any, List, Dict, Optional
from .command import AnimationColor


class Animation:
    None_: int
    Fill: int
    Blink: int
    Breathe: int
    RainbowCycle: int
    Comet: int
    Pulse: int


class LEDCommander:
    def SetColor(self, zone_id: str, color: AnimationColor) -> None: ...
    def SetGroupColor(self, group_id: str, color: AnimationColor) -> None: ...

    def SetAnimation(self, zone_id: str, animation: Animation, color: AnimationColor,
                     delay_ms: int = 250, reversed: bool = False, one_shot: bool = False) -> None: ...
    def SetGroupAnimation(self, group_id: str, animation: Animation, color: AnimationColor,
                          delay_ms: int = 250, reversed: bool = False, one_shot: bool = False) -> None: ...

    def SetAnimationSequence(self, zone_id: str, sequence_id: str) -> None: ...
    def SetGroupAnimationSequence(
        self, group_id: str, sequence_id: str) -> None: ...


class MatrixCommander:
    def SetText(self, zone_id: str, text: str, color: AnimationColor,
                direction: int = 0, delay_ms: int = 500, one_shot: bool = False) -> None: ...
    def SetGroupText(self, group_id: str, text: str, color: AnimationColor,
                     direction: int = 0, delay_ms: int = 500, one_shot: bool = False) -> None: ...


class ConnectorXInternal:
    def __init__(self) -> None: ...
    def GetEvents(self) -> List[Any]: ...
    def leds(self) -> LEDCommander: ...
    def matrix(self) -> Optional[MatrixCommander]: ...
    def GetLatestModuleData(self, module_id: str) -> List[Dict[str, Any]]: ...
    def RequestConfig(self, timeout_ms: int = 5000) -> Optional[str]: ...


ConnectorXInternal = ConnectorXInternal
