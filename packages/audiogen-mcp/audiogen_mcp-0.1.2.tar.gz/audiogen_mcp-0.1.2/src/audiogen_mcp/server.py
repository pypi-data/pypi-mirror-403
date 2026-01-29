"""
AudioGen MCP Server

An MCP server that generates sound effects from text descriptions using Meta's AudioGen model.
Designed for Apple Silicon Macs using MPS (Metal Performance Shaders) acceleration.
"""

# Mock xformers for Apple Silicon compatibility (xformers requires CUDA)
# audiocraft imports xformers but has a torch fallback for attention
import sys
from types import ModuleType

class _MockLowerTriangularMask:
    pass

class _MockOps(ModuleType):
    def __init__(self):
        super().__init__('xformers.ops')
        self.memory_efficient_attention = self._memory_efficient_attention
        self.LowerTriangularMask = _MockLowerTriangularMask
        # Add torch equivalents for xformers ops
        import torch
        self.unbind = torch.unbind

    @staticmethod
    def _memory_efficient_attention(*args, **kwargs):
        raise ImportError('xformers not available, use torch backend')

class _MockProfiler(ModuleType):
    def __init__(self):
        super().__init__('xformers.profiler')

    class profiler:
        class _Profiler:
            _CURRENT_PROFILER = None

class _MockXformers(ModuleType):
    def __init__(self):
        super().__init__('xformers')
        self.ops = _MockOps()
        self.profiler = _MockProfiler()

# Install mocks before any audiocraft imports
sys.modules['xformers'] = _MockXformers()
sys.modules['xformers.ops'] = sys.modules['xformers'].ops
sys.modules['xformers.profiler'] = sys.modules['xformers'].profiler

import asyncio
import base64
import hashlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    EmbeddedResource,
    BlobResourceContents,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("audiogen-mcp")

# Global model instance (lazy loaded)
_model = None
_model_lock = asyncio.Lock()

# Default output directory
DEFAULT_OUTPUT_DIR = Path.home() / "audiogen_outputs"


def get_device() -> str:
    """Determine the best available device for inference."""
    import torch
    if torch.backends.mps.is_available():
        logger.info("Using MPS (Metal Performance Shaders) for Apple Silicon")
        return "mps"
    elif torch.cuda.is_available():
        logger.info("Using CUDA")
        return "cuda"
    else:
        logger.warning("No GPU available, using CPU (this will be slow)")
        return "cpu"


async def get_model():
    """Lazy load the AudioGen model."""
    global _model
    async with _model_lock:
        if _model is None:
            logger.info("Loading AudioGen model (this may take a minute on first run)...")
            
            # Import here to avoid slow startup if model not needed
            from audiocraft.models import AudioGen
            
            device = get_device()
            _model = AudioGen.get_pretrained('facebook/audiogen-medium', device=device)
            logger.info("AudioGen model loaded successfully")
        return _model


def generate_filename(prompt: str, duration: float, format: str) -> str:
    """Generate a unique filename based on prompt hash and timestamp."""
    # Create a short hash of the prompt
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    # Sanitize prompt for filename (first 30 chars)
    safe_prompt = "".join(c if c.isalnum() or c in " -_" else "" for c in prompt[:30]).strip()
    safe_prompt = safe_prompt.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_prompt}_{prompt_hash}_{int(duration)}s_{timestamp}.{format}"


async def generate_sound_effect(
    prompt: str,
    duration: float = 5.0,
    output_dir: str | None = None,
    filename: str | None = None,
    format: str = "wav"
) -> dict[str, Any]:
    """
    Generate a sound effect from a text description.

    Args:
        prompt: Text description of the sound effect
        duration: Duration in seconds (1-30)
        output_dir: Directory to save the file (default: ~/audiogen_outputs)
        filename: Optional custom filename
        format: Output format (wav or ogg)

    Returns:
        Dictionary with file path, duration, and metadata
    """
    import torch
    import torchaudio
    
    # Validate duration
    duration = max(1.0, min(30.0, duration))
    
    # Set up output directory
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        filename = generate_filename(prompt, duration, format)
    elif not filename.endswith(f".{format}"):
        filename = f"{filename}.{format}"
    
    output_path = out_dir / filename
    
    # Get model and generate
    model = await get_model()
    model.set_generation_params(duration=duration)
    
    logger.info(f"Generating sound effect: '{prompt}' ({duration}s)")
    start_time = datetime.now()
    
    # Run generation in thread pool to not block event loop
    loop = asyncio.get_event_loop()
    wav = await loop.run_in_executor(None, lambda: model.generate([prompt]))
    
    generation_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Generation completed in {generation_time:.1f}s")
    
    # Get the generated audio (first item in batch)
    audio = wav[0].cpu()
    sample_rate = model.sample_rate
    
    # Save to file using scipy (torchaudio's new version requires torchcodec)
    from scipy.io import wavfile
    import numpy as np
    audio_np = audio.numpy()
    if audio_np.ndim == 2:
        audio_np = audio_np.T  # scipy expects (samples, channels)
    # Convert to int16 for wav
    audio_int16 = (audio_np * 32767).astype(np.int16)

    if format == 'ogg':
        # Save as WAV first, then convert to OGG using ffmpeg
        wav_temp_path = output_path.with_suffix('.wav.tmp')
        wavfile.write(str(wav_temp_path), sample_rate, audio_int16)
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', str(wav_temp_path),
                '-c:a', 'libvorbis', '-q:a', '4',
                str(output_path)
            ], check=True, capture_output=True)
            logger.info(f"Converted to OGG: {output_path}")
        finally:
            # Clean up temp WAV file
            if wav_temp_path.exists():
                wav_temp_path.unlink()
    else:
        # Save directly as WAV
        wavfile.write(str(output_path), sample_rate, audio_int16)

    logger.info(f"Saved to: {output_path}")
    
    return {
        "success": True,
        "file_path": str(output_path),
        "filename": filename,
        "prompt": prompt,
        "duration_requested": duration,
        "duration_actual": audio.shape[-1] / sample_rate,
        "sample_rate": sample_rate,
        "generation_time_seconds": generation_time,
        "format": format,
        "device": get_device(),
    }


async def list_generated_sounds(output_dir: str | None = None) -> list[dict]:
    """List all generated sound files."""
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    if not out_dir.exists():
        return []

    files = []
    for ext in ['*.wav', '*.mp3', '*.ogg']:
        for f in out_dir.glob(ext):
            stat = f.stat()
            files.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })

    # Sort by creation time, newest first
    files.sort(key=lambda x: x["created"], reverse=True)
    return files


# Create the MCP server
server = Server("audiogen-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_sound_effect",
            description="""Generate a sound effect from a text description using Meta's AudioGen AI model.

Best for: environmental sounds, foley, game sound effects, ambient audio.

Example prompts:
- "arcade game explosion, 8-bit style, retro"
- "whoosh sound, fast object passing by"
- "heartbeat, tense, dramatic, slow"
- "glass breaking, shatter"
- "footsteps on wooden floor"
- "thunder rumble, distant storm"
- "laser beam firing, sci-fi"
- "coin collecting, video game pickup sound"

Tips:
- Be specific and descriptive
- Include style keywords (retro, 8-bit, cinematic, realistic)
- Mention mood/tone (tense, cheerful, dramatic)
- Duration: 1-30 seconds (5s default, longer = slower generation)
- Generation takes ~60s per 5s of audio on Apple Silicon""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the sound effect to generate"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Duration in seconds (1-30, default: 5)",
                        "default": 5.0,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save the file (default: ~/audiogen_outputs)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Custom filename (without extension)"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: wav or ogg (default: wav)",
                        "enum": ["wav", "ogg"],
                        "default": "wav"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="generate_batch_sound_effects",
            description="""Generate multiple sound effects in one batch.

Useful for generating a set of related sounds at once.
Each sound is generated sequentially.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "sounds": {
                        "type": "array",
                        "description": "List of sound effect specifications",
                        "items": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string"},
                                "duration": {"type": "number", "default": 5.0},
                                "filename": {"type": "string"},
                                "format": {"type": "string", "enum": ["wav", "ogg"], "default": "wav"}
                            },
                            "required": ["prompt"]
                        }
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save all files"
                    },
                    "format": {
                        "type": "string",
                        "description": "Default output format for all sounds: wav or ogg (default: wav)",
                        "enum": ["wav", "ogg"],
                        "default": "wav"
                    }
                },
                "required": ["sounds"]
            }
        ),
        Tool(
            name="list_generated_sounds",
            description="List all previously generated sound effect files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to list (default: ~/audiogen_outputs)"
                    }
                }
            }
        ),
        Tool(
            name="get_model_status",
            description="Check if the AudioGen model is loaded and get device info.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "generate_sound_effect":
        try:
            result = await generate_sound_effect(
                prompt=arguments["prompt"],
                duration=arguments.get("duration", 5.0),
                output_dir=arguments.get("output_dir"),
                filename=arguments.get("filename"),
                format=arguments.get("format", "wav")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.exception("Error generating sound effect")
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))]
    
    elif name == "generate_batch_sound_effects":
        results = []
        sounds = arguments.get("sounds", [])
        output_dir = arguments.get("output_dir")
        default_format = arguments.get("format", "wav")

        for i, sound_spec in enumerate(sounds):
            logger.info(f"Generating sound {i+1}/{len(sounds)}: {sound_spec.get('prompt', '')[:50]}...")
            try:
                result = await generate_sound_effect(
                    prompt=sound_spec["prompt"],
                    duration=sound_spec.get("duration", 5.0),
                    output_dir=output_dir,
                    filename=sound_spec.get("filename"),
                    format=sound_spec.get("format", default_format)
                )
                results.append(result)
            except Exception as e:
                logger.exception(f"Error generating sound {i+1}")
                results.append({
                    "success": False,
                    "prompt": sound_spec.get("prompt"),
                    "error": str(e)
                })
        
        return [TextContent(type="text", text=json.dumps({
            "total": len(sounds),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results
        }, indent=2))]
    
    elif name == "list_generated_sounds":
        files = await list_generated_sounds(arguments.get("output_dir"))
        return [TextContent(type="text", text=json.dumps({
            "count": len(files),
            "files": files
        }, indent=2))]
    
    elif name == "get_model_status":
        import torch
        
        model_loaded = _model is not None
        device = get_device()
        
        status = {
            "model_loaded": model_loaded,
            "device": device,
            "mps_available": torch.backends.mps.is_available(),
            "cuda_available": torch.cuda.is_available(),
            "default_output_dir": str(DEFAULT_OUTPUT_DIR),
        }
        
        if model_loaded:
            status["model_name"] = "facebook/audiogen-medium"
            status["sample_rate"] = _model.sample_rate
        
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting AudioGen MCP Server...")
    logger.info(f"Default output directory: {DEFAULT_OUTPUT_DIR}")
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
