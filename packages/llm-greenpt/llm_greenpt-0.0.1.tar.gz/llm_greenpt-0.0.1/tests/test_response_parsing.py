"""Tests for parsing GreenPT API responses."""
import json
import pytest


# Sample non-streaming response from GreenPT API
SAMPLE_NON_STREAMING_RESPONSE = {
    "id": "chatcmpl-5db2808e-40f3-4de8-b2d3-e73d6b245d81",
    "object": "chat.completion",
    "created": 1769268774,
    "model": "green-l-raw",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?",
                "refusal": None,
                "tool_calls": [],
            },
            "logprobs": None,
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 8,
        "total_tokens": 62,
        "completion_tokens": 54,
        "inferenceTiming": {
            "inferenceTimeMs": 470.22690499946475
        }
    },
    "impact": {
        "version": "20250922",
        "inferenceTime": {
            "total": 470,
            "unit": "ms"
        },
        "energy": {
            "total": 121723,
            "unit": "Wms"
        },
        "emissions": {
            "total": 2,
            "unit": "ugCO2e"
        }
    }
}


class TestNonStreamingResponseParsing:
    """Test parsing of non-streaming GreenPT responses."""
    
    def test_impact_present_in_response(self):
        """Non-streaming responses should include impact data."""
        response = SAMPLE_NON_STREAMING_RESPONSE
        assert 'impact' in response
        
    def test_impact_structure(self):
        """Impact data should have the expected structure."""
        impact = SAMPLE_NON_STREAMING_RESPONSE['impact']
        
        assert impact['version'] == '20250922'
        assert impact['inferenceTime']['total'] == 470
        assert impact['inferenceTime']['unit'] == 'ms'
        assert impact['energy']['total'] == 121723
        assert impact['energy']['unit'] == 'Wms'
        assert impact['emissions']['total'] == 2
        assert impact['emissions']['unit'] == 'ugCO2e'
    
    def test_usage_has_inference_timing(self):
        """Usage should include inference timing details."""
        usage = SAMPLE_NON_STREAMING_RESPONSE['usage']
        
        assert 'inferenceTiming' in usage
        assert 'inferenceTimeMs' in usage['inferenceTiming']
        assert usage['inferenceTiming']['inferenceTimeMs'] > 0
    
    def test_token_counts(self):
        """Usage should include token counts."""
        usage = SAMPLE_NON_STREAMING_RESPONSE['usage']
        
        assert usage['prompt_tokens'] == 8
        assert usage['completion_tokens'] == 54
        assert usage['total_tokens'] == 62


class TestEnergyUnitConversions:
    """Test energy unit conversion calculations."""
    
    def test_wms_to_watt_hours(self):
        """Convert watt-milliseconds to watt-hours."""
        wms = 121723  # From sample response
        # 1 Wh = 3,600,000 Wms (1 hour = 3,600,000 ms)
        # So Wms / 3,600,000 = Wh
        wh = wms / 3_600_000
        expected = 121723 / 3_600_000  # ~0.0338 Wh
        assert abs(wh - expected) < 1e-10
        assert abs(wh - 0.0338119444) < 0.0001
    
    def test_wms_to_kilowatt_hours(self):
        """Convert watt-milliseconds to kilowatt-hours."""
        wms = 121723
        # 1 kWh = 3,600,000,000 Wms
        kwh = wms / 3_600_000_000
        expected = 121723 / 3_600_000_000  # ~3.38e-5 kWh
        assert abs(kwh - expected) < 1e-15
        assert abs(kwh - 3.38119e-5) < 1e-8
    
    def test_wms_to_joules(self):
        """Convert watt-milliseconds to joules."""
        wms = 121723
        # 1 Wms = 0.001 J (since 1 W = 1 J/s, and 1 ms = 0.001 s)
        joules = wms / 1000
        assert joules == 121.723
    
    def test_ugco2e_to_grams(self):
        """Convert micrograms CO2e to grams."""
        ugco2e = 2  # From sample response
        gco2e = ugco2e / 1_000_000
        assert gco2e == 0.000002


# Sample streaming response chunks from GreenPT API
SAMPLE_STREAMING_CHUNKS = [
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}',
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":"Hi"}}]}',
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":" there"}}]}',
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":"!"}}]}',
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[{"index":0,"delta":{"content":""},"finish_reason":"stop"}]}',
    # Final chunk with impact
    '{"id":"chatcmpl-ee3046fe","object":"chat.completion.chunk","created":1769268778,"model":"green-l-raw","choices":[],"usage":{"prompt_tokens":5,"total_tokens":19,"completion_tokens":14,"inferenceTiming":{"inferenceTimeMs":165.27840200066566}},"impact":{"version":"20250922","inferenceTime":{"total":165,"unit":"ms"},"energy":{"total":42784,"unit":"Wms"},"emissions":{"total":1,"unit":"ugCO2e"}}}',
]


class TestStreamingChunkParsing:
    """Test parsing of streaming chunks from GreenPT."""
    
    def test_content_chunks_have_delta(self):
        """Content chunks should have delta with content."""
        chunk = json.loads(SAMPLE_STREAMING_CHUNKS[1])
        assert 'choices' in chunk
        assert len(chunk['choices']) > 0
        assert 'delta' in chunk['choices'][0]
        assert chunk['choices'][0]['delta']['content'] == 'Hi'
    
    def test_final_chunk_has_impact(self):
        """The final streaming chunk should contain impact data."""
        final_chunk = json.loads(SAMPLE_STREAMING_CHUNKS[-1])
        
        assert 'impact' in final_chunk
        assert final_chunk['choices'] == []  # Empty choices in final chunk
    
    def test_final_chunk_has_usage(self):
        """The final streaming chunk should contain usage data."""
        final_chunk = json.loads(SAMPLE_STREAMING_CHUNKS[-1])
        
        assert 'usage' in final_chunk
        assert final_chunk['usage']['prompt_tokens'] == 5
        assert final_chunk['usage']['completion_tokens'] == 14
    
    def test_combine_content_from_chunks(self):
        """Content from all chunks should combine to form complete response."""
        combined_content = ""
        for chunk_str in SAMPLE_STREAMING_CHUNKS:
            chunk = json.loads(chunk_str)
            if chunk['choices']:
                content = chunk['choices'][0].get('delta', {}).get('content', '')
                if content:
                    combined_content += content
        
        assert combined_content == "Hi there!"
    
    def test_impact_in_final_chunk_only(self):
        """Impact should only be present in the final chunk."""
        for i, chunk_str in enumerate(SAMPLE_STREAMING_CHUNKS[:-1]):
            chunk = json.loads(chunk_str)
            assert 'impact' not in chunk, f"Chunk {i} should not have impact"
        
        final_chunk = json.loads(SAMPLE_STREAMING_CHUNKS[-1])
        assert 'impact' in final_chunk
