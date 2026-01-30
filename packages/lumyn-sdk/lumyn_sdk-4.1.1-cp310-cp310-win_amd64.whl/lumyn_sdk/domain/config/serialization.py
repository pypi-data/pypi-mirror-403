"""
JSON serialization and deserialization for DeviceConfig.

Handles conversion between DeviceConfig objects and JSON strings,
matching the Java vendordep JSON format exactly.
"""

import json
from typing import Dict, Any, Optional, List
from .models import (
    DeviceConfig,
    Network,
    Channel,
    Zone,
    AnimationColor,
    AnimationStep,
    AnimationSequence,
    Bitmap,
    Module,
    AnimationGroup,
)
from .enums import NetworkType, ZoneType, BitmapType


class ConfigSerializer:
    """Serialize/deserialize DeviceConfig to/from JSON"""

    @staticmethod
    def to_json(config: DeviceConfig) -> str:
        """Convert DeviceConfig to JSON string"""
        data = ConfigSerializer.to_dict(config)
        return json.dumps(data, indent=4)

    @staticmethod
    def from_json(json_str: str) -> DeviceConfig:
        """Parse JSON string to DeviceConfig"""
        data = json.loads(json_str)
        return ConfigSerializer.from_dict(data)

    @staticmethod
    def to_dict(config: DeviceConfig) -> Dict[str, Any]:
        """Convert DeviceConfig to dictionary"""
        result: Dict[str, Any] = {}

        # Team number
        if config.team_number:
            result["team"] = config.team_number

        # Network
        network_dict: Dict[str, Any] = {
            "mode": config.network.type.value.upper()  # "USB", "UART", etc.
        }
        if config.network.baud_rate is not None:
            network_dict["baudRate"] = config.network.baud_rate
        if config.network.address is not None:
            network_dict["address"] = config.network.address
        result["network"] = network_dict

        # Channels (as dictionary with string keys)
        if config.channels:
            channels_dict: Dict[str, Any] = {}
            for channel in config.channels:
                channel_dict: Dict[str, Any] = {
                    "id": channel.id,
                    "length": channel.length
                }
                if channel.brightness is not None:
                    channel_dict["brightness"] = channel.brightness

                # Zones
                if channel.zones:
                    zones_list = []
                    for zone in channel.zones:
                        zone_dict: Dict[str, Any] = {
                            "id": zone.id,
                            "type": zone.type.value
                        }
                        if zone.brightness is not None:
                            zone_dict["brightness"] = zone.brightness

                        if zone.type == ZoneType.STRIP:
                            zone_dict["length"] = zone.strip_length
                            if zone.reversed:
                                zone_dict["reversed"] = True
                        elif zone.type == ZoneType.MATRIX:
                            zone_dict["rows"] = zone.matrix_rows
                            zone_dict["cols"] = zone.matrix_cols
                            if zone.matrix_orientation:
                                zone_dict["orientation"] = zone.matrix_orientation

                        zones_list.append(zone_dict)
                    channel_dict["zones"] = zones_list

                channels_dict[channel.key] = channel_dict
            result["channels"] = channels_dict

        # Sequences
        if config.sequences:
            sequences_list = []
            for seq in config.sequences:
                seq_dict: Dict[str, Any] = {
                    "id": seq.id,
                    "steps": []
                }
                for step in seq.steps:
                    step_dict: Dict[str, Any] = {
                        "animationId": step.animation_id,
                        "delay": step.delay,
                        "reversed": step.reversed
                    }
                    if step.color:
                        step_dict["color"] = {
                            "r": step.color.r,
                            "g": step.color.g,
                            "b": step.color.b
                        }
                    if step.repeat is not None:
                        step_dict["repeat"] = step.repeat
                    seq_dict["steps"].append(step_dict)
                sequences_list.append(seq_dict)
            result["sequences"] = sequences_list

        # Bitmaps
        if config.bitmaps:
            bitmaps_list = []
            for bitmap in config.bitmaps:
                bitmap_dict: Dict[str, Any] = {
                    "id": bitmap.id,
                    "type": bitmap.type.value
                }
                if bitmap.type == BitmapType.STATIC:
                    if bitmap.path:
                        bitmap_dict["path"] = bitmap.path
                elif bitmap.type == BitmapType.ANIMATED:
                    if bitmap.folder:
                        bitmap_dict["folder"] = bitmap.folder
                    if bitmap.frame_delay is not None:
                        bitmap_dict["delay"] = bitmap.frame_delay
                bitmaps_list.append(bitmap_dict)
            result["bitmaps"] = bitmaps_list

        # Modules (called "sensors" in JSON)
        if config.modules:
            sensors_list = []
            for module in config.modules:
                sensor_dict: Dict[str, Any] = {
                    "id": module.id,
                    "type": module.type,
                    "pollingRateMs": module.polling_rate_ms,
                    "connection": module.connection_type
                }
                if module.config:
                    sensor_dict["config"] = module.config
                sensors_list.append(sensor_dict)
            result["sensors"] = sensors_list

        # Groups
        if config.groups:
            groups_list = []
            for group in config.groups:
                group_dict: Dict[str, Any] = {
                    "id": group.id,
                    "zoneIds": group.zone_ids.copy()
                }
                groups_list.append(group_dict)
            result["groups"] = groups_list

        # MD5 (not typically in JSON, but included if present)
        if config.md5:
            # Convert bytes to hex string for JSON
            result["md5"] = config.md5.hex()

        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> DeviceConfig:
        """Create DeviceConfig from dictionary"""
        # Network
        network_data = data.get("network", {})
        network_mode_str = network_data.get("mode", "USB").upper()
        # Map uppercase JSON values to enum
        network_type_map = {
            "USB": NetworkType.USB,
            "UART": NetworkType.UART,
            "I2C": NetworkType.I2C,
            "CAN": NetworkType.CAN,
        }
        network_type = network_type_map.get(network_mode_str, NetworkType.USB)
        network = Network(
            type=network_type,
            address=network_data.get("address"),
            baud_rate=network_data.get("baudRate")
        )

        # Channels
        channels = []
        channels_data = data.get("channels", {})
        for key, channel_data in channels_data.items():
            zones = []
            for zone_data in channel_data.get("zones", []):
                zone_type_str = zone_data.get("type", "strip").lower()
                zone_type = ZoneType.STRIP if zone_type_str == "strip" else ZoneType.MATRIX

                zone = Zone(
                    type=zone_type,
                    id=zone_data["id"],
                    brightness=zone_data.get("brightness"),
                    strip_length=zone_data.get("length", 0),
                    reversed=zone_data.get("reversed", False),
                    matrix_rows=zone_data.get("rows", 0),
                    matrix_cols=zone_data.get("cols", 0),
                    matrix_orientation=zone_data.get("orientation")
                )
                zones.append(zone)

            channel = Channel(
                key=key,
                id=channel_data.get("id", key),
                length=channel_data["length"],
                brightness=channel_data.get("brightness"),
                zones=zones
            )
            channels.append(channel)

        # Sequences
        sequences = []
        for seq_data in data.get("sequences", []):
            steps = []
            for step_data in seq_data.get("steps", []):
                color_data = step_data.get("color")
                color = None
                if color_data:
                    color = AnimationColor(
                        r=color_data["r"],
                        g=color_data["g"],
                        b=color_data["b"]
                    )

                step = AnimationStep(
                    animation_id=step_data["animationId"],
                    color=color,
                    delay=step_data.get("delay", 100),
                    reversed=step_data.get("reversed", False),
                    repeat=step_data.get("repeat")
                )
                steps.append(step)

            sequence = AnimationSequence(
                id=seq_data["id"],
                steps=steps
            )
            sequences.append(sequence)

        # Bitmaps
        bitmaps = []
        for bitmap_data in data.get("bitmaps", []):
            bitmap_type_str = bitmap_data.get("type", "static").lower()
            bitmap_type = BitmapType.STATIC if bitmap_type_str == "static" else BitmapType.ANIMATED

            bitmap = Bitmap(
                id=bitmap_data["id"],
                type=bitmap_type,
                path=bitmap_data.get("path"),
                folder=bitmap_data.get("folder"),
                frame_delay=bitmap_data.get("delay")
            )
            bitmaps.append(bitmap)

        # Modules (called "sensors" in JSON)
        modules = []
        for sensor_data in data.get("sensors", []):
            module = Module(
                id=sensor_data["id"],
                type=sensor_data["type"],
                polling_rate_ms=sensor_data["pollingRateMs"],
                connection_type=sensor_data["connection"],
                config=sensor_data.get("config")
            )
            modules.append(module)

        # Groups
        groups = []
        for group_data in data.get("groups", []):
            group = AnimationGroup(
                id=group_data["id"],
                zone_ids=group_data.get("zoneIds", [])
            )
            groups.append(group)

        # MD5
        md5 = None
        if "md5" in data:
            md5_hex = data["md5"]
            if isinstance(md5_hex, str):
                md5 = bytes.fromhex(md5_hex)
            elif isinstance(md5_hex, bytes):
                md5 = md5_hex

        return DeviceConfig(
            network=network,
            channels=channels,
            md5=md5,
            team_number=data.get("team"),
            sequences=sequences,
            bitmaps=bitmaps,
            modules=modules,
            groups=groups
        )
