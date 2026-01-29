"""Tests for streaming impact data capture in llm-greenpt."""
import json
import pytest
from llm_greenpt import ImpactCapturingSSEDecoder


class TestImpactCapturingSSEDecoder:
    """Test the custom SSE decoder that captures GreenPT impact data."""

    def test_captures_impact_from_data_line(self):
        """Impact data in SSE data lines should be captured and stored."""
        decoder = ImpactCapturingSSEDecoder()
        line = 'data: {"id":"test","choices":[],"impact":{"version":"20250922","inferenceTime":{"total":156,"unit":"ms"},"energy":{"total":40433,"unit":"Wms"},"emissions":{"total":1,"unit":"ugCO2e"}}}'
        result = decoder.decode(line)
        
        # Should still emit the event (unlike Neuralwatt which returns None for comments)
        # The impact is captured separately
        assert decoder.impact_data is not None
        assert decoder.impact_data['version'] == '20250922'
        assert decoder.impact_data['energy']['total'] == 40433
        assert decoder.impact_data['energy']['unit'] == 'Wms'
        assert decoder.impact_data['emissions']['total'] == 1
        assert decoder.impact_data['emissions']['unit'] == 'ugCO2e'

    def test_ignores_data_without_impact(self):
        """Regular data lines without impact should not set impact_data."""
        decoder = ImpactCapturingSSEDecoder()
        line = 'data: {"id":"test","choices":[{"delta":{"content":"Hello"}}]}'
        decoder.decode(line)
        
        assert decoder.impact_data is None

    def test_passes_data_lines_to_parent(self):
        """Standard data lines should be handled by parent decoder."""
        decoder = ImpactCapturingSSEDecoder()
        
        # Decode a data line and then empty line to flush (SSE spec)
        decoder.decode('data: {"test": "value"}')
        result = decoder.decode('')
        
        assert result is not None
        assert result.data == '{"test": "value"}'

    def test_handles_malformed_json(self):
        """Malformed JSON in data lines should not crash."""
        decoder = ImpactCapturingSSEDecoder()
        result = decoder.decode('data: {not valid json}')
        
        # Should not crash, impact_data should remain None
        assert decoder.impact_data is None

    def test_impact_data_initially_none(self):
        """Impact data should be None before any impact-containing line is seen."""
        decoder = ImpactCapturingSSEDecoder()
        assert decoder.impact_data is None

    def test_ignores_done_marker(self):
        """The [DONE] marker should not affect impact data."""
        decoder = ImpactCapturingSSEDecoder()
        result = decoder.decode('data: [DONE]')
        
        assert decoder.impact_data is None

    def test_full_streaming_sequence(self):
        """Test a realistic streaming sequence from GreenPT."""
        decoder = ImpactCapturingSSEDecoder()
        
        # Simulate typical GreenPT streaming response
        lines = [
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}',
            '',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":"Hi"}}]}',
            '',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":" there"}}]}',
            '',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":"!"}}]}',
            '',
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":""},"finish_reason":"stop"}]}',
            '',
            # Final chunk with impact data
            'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[],"usage":{"prompt_tokens":5,"total_tokens":19,"completion_tokens":14},"impact":{"version":"20250922","inferenceTime":{"total":165,"unit":"ms"},"energy":{"total":42784,"unit":"Wms"},"emissions":{"total":1,"unit":"ugCO2e"}}}',
            '',
        ]
        
        # Process all lines
        for line in lines:
            decoder.decode(line)
        
        # Impact should be captured from the final chunk
        assert decoder.impact_data is not None
        assert decoder.impact_data['version'] == '20250922'
        assert decoder.impact_data['inferenceTime']['total'] == 165
        assert decoder.impact_data['inferenceTime']['unit'] == 'ms'
        assert decoder.impact_data['energy']['total'] == 42784
        assert decoder.impact_data['energy']['unit'] == 'Wms'
        assert decoder.impact_data['emissions']['total'] == 1
        assert decoder.impact_data['emissions']['unit'] == 'ugCO2e'

    def test_inference_time_extraction(self):
        """Test that inference time is properly extracted."""
        decoder = ImpactCapturingSSEDecoder()
        line = 'data: {"choices":[],"impact":{"version":"20250922","inferenceTime":{"total":500,"unit":"ms"},"energy":{"total":100000,"unit":"Wms"},"emissions":{"total":5,"unit":"ugCO2e"}}}'
        decoder.decode(line)
        
        assert decoder.impact_data['inferenceTime']['total'] == 500
        assert decoder.impact_data['inferenceTime']['unit'] == 'ms'

    def test_emissions_extraction(self):
        """Test that emissions data is properly extracted."""
        decoder = ImpactCapturingSSEDecoder()
        line = 'data: {"choices":[],"impact":{"version":"20250922","inferenceTime":{"total":200,"unit":"ms"},"energy":{"total":50000,"unit":"Wms"},"emissions":{"total":10,"unit":"ugCO2e"}}}'
        decoder.decode(line)
        
        assert decoder.impact_data['emissions']['total'] == 10
        assert decoder.impact_data['emissions']['unit'] == 'ugCO2e'


class TestImpactDataStructure:
    """Test that impact data follows the expected GreenPT structure."""
    
    def test_impact_has_required_fields(self):
        """Verify the expected impact data structure."""
        decoder = ImpactCapturingSSEDecoder()
        line = 'data: {"choices":[],"impact":{"version":"20250922","inferenceTime":{"total":156,"unit":"ms"},"energy":{"total":40433,"unit":"Wms"},"emissions":{"total":1,"unit":"ugCO2e"}}}'
        decoder.decode(line)
        
        impact = decoder.impact_data
        
        # Check required top-level fields
        assert 'version' in impact
        assert 'inferenceTime' in impact
        assert 'energy' in impact
        assert 'emissions' in impact
        
        # Check nested structure
        assert 'total' in impact['inferenceTime']
        assert 'unit' in impact['inferenceTime']
        assert 'total' in impact['energy']
        assert 'unit' in impact['energy']
        assert 'total' in impact['emissions']
        assert 'unit' in impact['emissions']
