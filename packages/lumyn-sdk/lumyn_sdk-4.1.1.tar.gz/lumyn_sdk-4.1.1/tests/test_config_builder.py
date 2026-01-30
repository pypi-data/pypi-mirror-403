"""
Unit tests for configuration builder API.
"""

import pytest
from lumyn_sdk import (
    ConfigBuilder,
    SerializeConfigToJson,
    ParseConfig,
    LumynConfiguration,
    NetworkType,
    ZoneType,
    BitmapType,
)


class TestConfigBuilder:
    """Test ConfigBuilder root builder"""

    def test_basic_config(self):
        """Test creating a basic configuration"""
        config = ConfigBuilder() \
            .ForTeam("9999") \
            .SetNetworkType(NetworkType.USB) \
            .AddChannel(0, "channel_0", 144) \
                .Brightness(255) \
                .AddStripZone("main", 144, False) \
                .EndChannel() \
            .Build()

        assert config.teamNumber == "9999"
        assert config.network.type == NetworkType.USB
        assert len(config.channels) == 1
        assert config.channels[0].id == "channel_0"
        assert config.channels[0].length == 144
        assert config.channels[0].brightness == 255
        assert len(config.channels[0].zones) == 1
        assert config.channels[0].zones[0].id == "main"
        assert config.channels[0].zones[0].type == ZoneType.STRIP

    def test_baud_rate_validation(self):
        """Test baud rate validation"""
        config_valid = ConfigBuilder() \
            .SetNetworkType(NetworkType.UART) \
            .SetBaudRate(115200) \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .Build()

        assert config_valid.network.uart.baud == 115200

        # Invalid baud rate should default to 115200
        config_invalid = ConfigBuilder() \
            .SetNetworkType(NetworkType.UART) \
            .SetBaudRate(12345) \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .Build()

        assert config_invalid.network.uart.baud == 115200

    def test_brightness_clamping(self):
        """Test brightness clamping to 0-255"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .Brightness(300) \
                .AddStripZone("zone1", 100, False, 500) \
                .EndChannel() \
            .Build()

        assert config.channels[0].brightness == 255
        assert config.channels[0].zones[0].brightness == 255

        config2 = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .Brightness(-10) \
                .AddStripZone("zone1", 100, False, -5) \
                .EndChannel() \
            .Build()

        assert config2.channels[0].brightness == 0
        assert config2.channels[0].zones[0].brightness == 0

    def test_i2c_address_clamping(self):
        """Test I2C address clamping to 0-255"""
        config = ConfigBuilder() \
            .SetNetworkType(NetworkType.I2C) \
            .SetI2cAddress(300) \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .Build()

        assert config.network.address == 255

        config2 = ConfigBuilder() \
            .SetNetworkType(NetworkType.I2C) \
            .SetI2cAddress(-10) \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .Build()

        assert config2.network.address == 0

    def test_multiple_channels(self):
        """Test adding multiple channels"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddChannel(1, "ch1", 200) \
                .AddStripZone("zone2", 200) \
                .EndChannel() \
            .Build()

        assert len(config.channels) == 2
        assert config.channels[0].key == "0"
        assert config.channels[1].key == "1"

    def test_matrix_zone(self):
        """Test adding matrix zones"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 64) \
                .AddMatrixZone("matrix1", 8, 8, 100) \
                .EndChannel() \
            .Build()

        zone = config.channels[0].zones[0]
        assert zone.type == ZoneType.MATRIX
        assert zone.matrix_rows == 8
        assert zone.matrix_cols == 8
        assert zone.brightness == 100

    def test_matrix_zone_with_orientation(self):
        """Test adding matrix zone with orientation"""
        orientation = {
            "cornerTopBottom": "top",
            "cornerLeftRight": "left",
            "axisLayout": "rows",
            "sequenceLayout": "zigzag"
        }

        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 64) \
                .AddMatrixZone("matrix1", 8, 8, 100, orientation) \
                .EndChannel() \
            .Build()

        zone = config.channels[0].zones[0]
        assert zone.matrix_orientation == orientation


class TestSequenceBuilder:
    """Test animation sequence builders"""

    def test_simple_sequence(self):
        """Test creating a simple sequence"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddSequence("startup") \
                .AddStep("Fill") \
                    .WithColor(255, 0, 0) \
                    .WithDelay(100) \
                    .EndStep() \
                .EndSequence() \
            .Build()

        assert len(config.sequences) == 1
        seq = config.sequences[0]
        assert seq.id == "startup"
        assert len(seq.steps) == 1
        assert seq.steps[0].animation_id == "Fill"
        assert seq.steps[0].color.r == 255
        assert seq.steps[0].color.g == 0
        assert seq.steps[0].color.b == 0

    def test_sequence_with_multiple_steps(self):
        """Test sequence with multiple steps"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddSequence("startup") \
                .AddStep("FadeIn") \
                    .WithColor(0, 255, 0) \
                    .WithDelay(30) \
                    .WithRepeat(1) \
                    .EndStep() \
                .AddStep("Fill") \
                    .WithColor(0, 255, 0) \
                    .WithDelay(-1) \
                    .Reverse(False) \
                    .WithRepeat(0) \
                    .EndStep() \
                .EndSequence() \
            .Build()

        seq = config.sequences[0]
        assert len(seq.steps) == 2
        assert seq.steps[0].animation_id == "FadeIn"
        assert seq.steps[0].repeat == 1
        assert seq.steps[1].animation_id == "Fill"
        assert seq.steps[1].repeat == 0

    def test_color_clamping(self):
        """Test color component clamping"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddSequence("test") \
                .AddStep("Fill") \
                    .WithColor(300, -10, 500) \
                    .EndStep() \
                .EndSequence() \
            .Build()

        color = config.sequences[0].steps[0].color
        assert color.r == 255
        assert color.g == 0
        assert color.b == 255


class TestBitmapBuilder:
    """Test bitmap builders"""

    def test_static_bitmap(self):
        """Test creating static bitmap"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddBitmap("logo") \
                .Static("logo.bmp") \
                .EndBitmap() \
            .Build()

        assert len(config.bitmaps) == 1
        bitmap = config.bitmaps[0]
        assert bitmap.id == "logo"
        assert bitmap.type == BitmapType.STATIC
        assert bitmap.path == "logo.bmp"
        assert bitmap.folder is None

    def test_animated_bitmap(self):
        """Test creating animated bitmap"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddBitmap("pikachu") \
                .Animated("pikachu_16x16", 100) \
                .EndBitmap() \
            .Build()

        bitmap = config.bitmaps[0]
        assert bitmap.type == BitmapType.ANIMATED
        assert bitmap.folder == "pikachu_16x16"
        assert bitmap.frame_delay == 100
        assert bitmap.path is None


class TestModuleBuilder:
    """Test module builders"""

    def test_module_without_config(self):
        """Test creating module without custom config"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddModule("sensor1", "VL53L1X", 50, "I2C") \
                .EndModule() \
            .Build()

        assert len(config.modules) == 1
        module = config.modules[0]
        assert module.id == "sensor1"
        assert module.type == "VL53L1X"
        assert module.polling_rate_ms == 50
        assert module.connection_type == "I2C"
        assert module.config is None

    def test_module_with_config(self):
        """Test creating module with custom config"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddModule("sensor1", "VL53L1X", 50, "I2C") \
                .WithConfig("address", "0x29") \
                .WithConfig("mode", "long_range") \
                .EndModule() \
            .Build()

        module = config.modules[0]
        assert module.config is not None
        assert module.config["address"] == "0x29"
        assert module.config["mode"] == "long_range"

    def test_polling_rate_validation(self):
        """Test polling rate validation (should be >= 0)"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 100) \
                .AddStripZone("zone1", 100) \
                .EndChannel() \
            .AddModule("sensor1", "VL53L1X", -10, "I2C") \
                .EndModule() \
            .Build()

        assert config.modules[0].polling_rate_ms == 0


class TestGroupBuilder:
    """Test group builders"""

    def test_group_with_zones(self):
        """Test creating zone group"""
        config = ConfigBuilder() \
            .AddChannel(0, "ch0", 200) \
                .AddStripZone("zone1", 100) \
                .AddStripZone("zone2", 100) \
                .EndChannel() \
            .AddGroup("all_zones") \
                .AddZone("zone1") \
                .AddZone("zone2") \
                .EndGroup() \
            .Build()

        assert len(config.groups) == 1
        group = config.groups[0]
        assert group.id == "all_zones"
        assert len(group.zone_ids) == 2
        assert "zone1" in group.zone_ids
        assert "zone2" in group.zone_ids


class TestJSONSerialization:
    """Test JSON serialization and deserialization"""

    def test_round_trip(self):
        """Test serializing and deserializing config"""
        original = ConfigBuilder() \
            .ForTeam("9999") \
            .SetNetworkType(NetworkType.USB) \
            .AddChannel(0, "channel_0", 144) \
                .Brightness(255) \
                .AddStripZone("main", 144, False) \
                .EndChannel() \
            .AddSequence("startup") \
                .AddStep("Fill") \
                    .WithColor(255, 0, 0) \
                    .WithDelay(100) \
                    .EndStep() \
                .EndSequence() \
            .AddGroup("all_leds") \
                .AddZone("main") \
                .EndGroup() \
            .Build()

        # Serialize to JSON
        json_str = SerializeConfigToJson(original)

        # Deserialize from JSON
        restored = ParseConfig(json_str)

        # Verify round trip
        assert restored.teamNumber == original.teamNumber
        assert restored.network.type == original.network.type
        assert len(restored.channels) == len(original.channels)
        assert len(restored.sequences) == len(original.sequences)
        assert len(restored.groups) == len(original.groups)

    def test_json_format_matches_java(self):
        """Test that JSON format matches Java vendordep format"""
        config = ConfigBuilder() \
            .ForTeam("9999") \
            .SetNetworkType(NetworkType.USB) \
            .AddChannel(1, "1", 144) \
                .Brightness(100) \
                .AddStripZone("main", 144, False, 100) \
                .EndChannel() \
            .Build()

        json_str = SerializeConfigToJson(config)
        import json
        data = json.loads(json_str)

        # Check format matches expected structure
        assert data["team"] == "9999"
        assert data["network"]["mode"] == "USB"
        assert "1" in data["channels"]
        assert data["channels"]["1"]["id"] == "1"
        assert data["channels"]["1"]["length"] == 144
        assert data["channels"]["1"]["brightness"] == 100
        assert len(data["channels"]["1"]["zones"]) == 1
        assert data["channels"]["1"]["zones"][0]["type"] == "strip"
        assert data["channels"]["1"]["zones"][0]["id"] == "main"
