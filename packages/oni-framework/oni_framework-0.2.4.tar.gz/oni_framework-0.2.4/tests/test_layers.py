"""Tests for the layers module."""

import pytest

from oni.layers import ONIStack, Layer, Domain


class TestLayer:
    """Tests for the Layer dataclass."""

    def test_layer_creation(self):
        """Should create a layer with required fields."""
        layer = Layer(
            number=1,
            name="Test",
            domain=Domain.BIOLOGICAL,
            function="Test function",
        )
        assert layer.number == 1
        assert layer.name == "Test"
        assert layer.domain == Domain.BIOLOGICAL

    def test_is_biological(self):
        """Should correctly identify biological layers."""
        layer = Layer(number=1, name="Test", domain=Domain.BIOLOGICAL, function="")
        assert layer.is_biological
        assert not layer.is_silicon
        assert not layer.is_bridge

    def test_is_silicon(self):
        """Should correctly identify silicon layers."""
        layer = Layer(number=10, name="Test", domain=Domain.SILICON, function="")
        assert layer.is_silicon
        assert not layer.is_biological
        assert not layer.is_bridge

    def test_is_bridge(self):
        """Should correctly identify bridge layer."""
        layer = Layer(number=8, name="Test", domain=Domain.BRIDGE, function="")
        assert layer.is_bridge
        assert not layer.is_biological
        assert not layer.is_silicon


class TestONIStack:
    """Tests for the ONIStack class."""

    def test_has_14_layers(self):
        """Stack should have exactly 14 layers."""
        stack = ONIStack()
        assert len(stack) == 14

    def test_layer_access_by_number(self):
        """Should access layers by number."""
        stack = ONIStack()
        layer8 = stack.layer(8)
        assert layer8.number == 8
        assert layer8.name == "Neural Gateway"

    def test_layer_access_by_index(self):
        """Should access layers via indexing."""
        stack = ONIStack()
        assert stack[1].number == 1
        assert stack[14].number == 14

    def test_invalid_layer_raises(self):
        """Should raise KeyError for invalid layer numbers."""
        stack = ONIStack()
        with pytest.raises(KeyError):
            stack.layer(0)
        with pytest.raises(KeyError):
            stack.layer(15)

    def test_iteration(self):
        """Should iterate through all layers in order."""
        stack = ONIStack()
        layers = list(stack)
        assert len(layers) == 14
        assert [l.number for l in layers] == list(range(1, 15))

    def test_biological_layers(self):
        """Should return layers 1-7 as biological."""
        stack = ONIStack()
        bio = stack.biological_layers()
        assert len(bio) == 7
        assert all(l.is_biological for l in bio)
        assert [l.number for l in bio] == list(range(1, 8))

    def test_silicon_layers(self):
        """Should return layers 9-14 as silicon."""
        stack = ONIStack()
        sil = stack.silicon_layers()
        assert len(sil) == 6
        assert all(l.is_silicon for l in sil)
        assert [l.number for l in sil] == list(range(9, 15))

    def test_bridge_layer(self):
        """Should return layer 8 as bridge."""
        stack = ONIStack()
        bridge = stack.bridge_layer()
        assert bridge.number == 8
        assert bridge.is_bridge

    def test_firewall_layer(self):
        """Firewall layer should be layer 8."""
        stack = ONIStack()
        fw = stack.firewall_layer()
        assert fw.number == 8
        assert fw.metadata.get("firewall_layer") is True

    def test_layer_names(self):
        """Should have expected layer names."""
        stack = ONIStack()
        expected_names = [
            "Molecular", "Cellular", "Microcircuit", "Regional",
            "Systems", "Whole-Brain", "Behavioral", "Neural Gateway",
            "Signal Processing", "Protocol", "Transport", "Session",
            "Presentation", "Application"
        ]
        actual_names = [stack[i].name for i in range(1, 15)]
        assert actual_names == expected_names

    def test_get_attack_surfaces(self):
        """Should return attack surfaces for layers."""
        stack = ONIStack()
        surfaces = stack.get_attack_surfaces((8, 8))
        assert 8 in surfaces
        assert len(surfaces[8]) > 0

    def test_get_defenses(self):
        """Should return defenses for layers."""
        stack = ONIStack()
        defenses = stack.get_defenses((8, 8))
        assert 8 in defenses
        assert len(defenses[8]) > 0

    def test_ascii_diagram(self):
        """Should generate ASCII diagram."""
        stack = ONIStack()
        diagram = stack.ascii_diagram()
        assert "ONI FRAMEWORK" in diagram
        assert "L 8" in diagram or "L8" in diagram.replace(" ", "")
        assert "Neural Gateway" in diagram or "NEURAL GATEWAY" in diagram

    def test_summary(self):
        """Should generate summary text."""
        stack = ONIStack()
        summary = stack.summary()
        assert "14" in summary
        assert "Biological" in summary
        assert "Silicon" in summary
