"""
Tests for A2UI Image Generation Agent
"""

import pytest
from agent import ImageGenerationAgent, ColorTone


class TestWidgetDetection:
    """Test widget detection logic"""
    
    def setup_method(self):
        """Setup test agent"""
        self.agent = ImageGenerationAgent(api_key="test_key")
    
    def test_color_detection(self):
        """Test color tone widget detection"""
        test_cases = [
            ("Generate with blue tone", True, False),
            ("Create warm colors", True, False),
            ("Make it more saturated", True, False),
            ("Adjust the hue", True, False),
            ("Generate a cat", False, False),
        ]
        
        for prompt, expected_color, expected_sketch in test_cases:
            result = self.agent.analyze_request(prompt)
            assert result['needs_color_control'] == expected_color, \
                f"Failed for: {prompt}"
            assert result['needs_sketch_board'] == expected_sketch, \
                f"Failed for: {prompt}"
    
    def test_sketch_detection(self):
        """Test sketch board widget detection"""
        test_cases = [
            ("Draw an outline", False, True),
            ("Place the tree on the left", False, True),
            ("Specific composition needed", False, True),
            ("Position the elements", False, True),
            ("Generate a sunset", False, False),
        ]
        
        for prompt, expected_color, expected_sketch in test_cases:
            result = self.agent.analyze_request(prompt)
            assert result['needs_color_control'] == expected_color, \
                f"Failed for: {prompt}"
            assert result['needs_sketch_board'] == expected_sketch, \
                f"Failed for: {prompt}"
    
    def test_both_widgets(self):
        """Test detection of both widgets"""
        prompt = "Create with blue tone and specific layout composition"
        result = self.agent.analyze_request(prompt)
        assert result['needs_color_control'] == True
        assert result['needs_sketch_board'] == True
    
    def test_neither_widget(self):
        """Test when no widgets needed"""
        prompt = "Generate an image of a sunset"
        result = self.agent.analyze_request(prompt)
        assert result['needs_color_control'] == False
        assert result['needs_sketch_board'] == False


class TestA2UIMessage:
    """Test A2UI message generation"""
    
    def setup_method(self):
        """Setup test agent"""
        self.agent = ImageGenerationAgent(api_key="test_key")
    
    def test_basic_message(self):
        """Test basic message without widgets"""
        message = self.agent.generate_a2ui_message(
            text="Here's your image",
            show_color_control=False,
            show_sketch_board=False
        )
        
        assert message["role"] == "assistant"
        assert len(message["parts"]) == 1
        assert message["parts"][0]["text"] == "Here's your image"
    
    def test_message_with_color_widget(self):
        """Test message with color tone widget"""
        message = self.agent.generate_a2ui_message(
            text="Adjust the colors",
            show_color_control=True,
            show_sketch_board=False
        )
        
        assert len(message["parts"]) == 2
        assert "a2ui" in message["parts"][1]
        assert message["parts"][1]["a2ui"]["type"] == "color-tone-control"
    
    def test_message_with_sketch_widget(self):
        """Test message with sketch board widget"""
        message = self.agent.generate_a2ui_message(
            text="Draw your composition",
            show_color_control=False,
            show_sketch_board=True
        )
        
        assert len(message["parts"]) == 2
        assert "a2ui" in message["parts"][1]
        assert message["parts"][1]["a2ui"]["type"] == "sketch-board"
    
    def test_message_with_both_widgets(self):
        """Test message with both widgets"""
        message = self.agent.generate_a2ui_message(
            text="Fine-tune your image",
            show_color_control=True,
            show_sketch_board=True
        )
        
        assert len(message["parts"]) == 3  # text + 2 widgets
        widget_types = [
            part["a2ui"]["type"] 
            for part in message["parts"] 
            if "a2ui" in part
        ]
        assert "color-tone-control" in widget_types
        assert "sketch-board" in widget_types
    
    def test_message_with_image(self):
        """Test message with inline image"""
        message = self.agent.generate_a2ui_message(
            text="Your image",
            image_data="base64_encoded_data",
            show_color_control=False,
            show_sketch_board=False
        )
        
        assert len(message["parts"]) == 2
        assert "inlineData" in message["parts"][1]
        assert message["parts"][1]["inlineData"]["mimeType"] == "image/png"


class TestColorTone:
    """Test ColorTone dataclass"""
    
    def test_color_tone_creation(self):
        """Test creating a ColorTone"""
        tone = ColorTone(
            hue=180.0,
            saturation=50.0,
            lightness=60.0,
            temperature="cool"
        )
        
        assert tone.hue == 180.0
        assert tone.saturation == 50.0
        assert tone.lightness == 60.0
        assert tone.temperature == "cool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
