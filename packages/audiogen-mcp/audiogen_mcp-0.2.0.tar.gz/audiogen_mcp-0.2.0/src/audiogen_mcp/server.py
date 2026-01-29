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
import hashlib
import json
import logging
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("audiogen-mcp")

# Global model instance (lazy loaded)
_model = None
_model_lock = threading.Lock()

# Background jobs storage
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()

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


def get_model():
    """Get or load the AudioGen model (thread-safe)."""
    global _model
    with _model_lock:
        if _model is None:
            logger.info("Loading AudioGen model (this may take a minute on first run)...")
            from audiocraft.models import AudioGen
            device = get_device()
            _model = AudioGen.get_pretrained('facebook/audiogen-medium', device=device)
            logger.info("AudioGen model loaded successfully")
        return _model


def generate_filename(prompt: str, duration: float, format: str) -> str:
    """Generate a unique filename based on prompt hash and timestamp."""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    safe_prompt = "".join(c if c.isalnum() or c in " -_" else "" for c in prompt[:30]).strip()
    safe_prompt = safe_prompt.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_prompt}_{prompt_hash}_{int(duration)}s_{timestamp}.{format}"


def _run_generation(job_id: str, prompt: str, duration: float, output_dir: Path, filename: str, format: str):
    """Run generation in background thread."""
    import numpy as np
    from scipy.io import wavfile

    try:
        with _jobs_lock:
            _jobs[job_id]["status"] = "loading_model"

        model = get_model()
        model.set_generation_params(duration=duration)

        with _jobs_lock:
            _jobs[job_id]["status"] = "generating"
            _jobs[job_id]["message"] = f"Generating {duration}s of audio..."

        logger.info(f"[{job_id}] Generating: '{prompt}' ({duration}s)")
        start_time = datetime.now()

        wav = model.generate([prompt])

        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{job_id}] Generation completed in {generation_time:.1f}s")

        with _jobs_lock:
            _jobs[job_id]["status"] = "saving"
            _jobs[job_id]["message"] = "Saving audio file..."

        # Get the generated audio
        audio = wav[0].cpu()
        sample_rate = model.sample_rate

        # Convert to numpy
        audio_np = audio.numpy()
        if audio_np.ndim == 2:
            audio_np = audio_np.T
        audio_int16 = (audio_np * 32767).astype(np.int16)

        output_path = output_dir / filename

        if format == 'ogg':
            wav_temp_path = output_path.with_suffix('.wav.tmp')
            wavfile.write(str(wav_temp_path), sample_rate, audio_int16)
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', str(wav_temp_path),
                    '-c:a', 'libvorbis', '-q:a', '4',
                    str(output_path)
                ], check=True, capture_output=True)
            finally:
                if wav_temp_path.exists():
                    wav_temp_path.unlink()
        else:
            wavfile.write(str(output_path), sample_rate, audio_int16)

        logger.info(f"[{job_id}] Saved to: {output_path}")

        # Update job as completed
        with _jobs_lock:
            _jobs[job_id].update({
                "status": "completed",
                "message": "Generation complete",
                "result": {
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
            })

    except Exception as e:
        logger.exception(f"[{job_id}] Generation failed")
        with _jobs_lock:
            _jobs[job_id].update({
                "status": "failed",
                "message": str(e),
                "result": {
                    "success": False,
                    "error": str(e)
                }
            })


def start_generation(
    prompt: str,
    duration: float = 5.0,
    output_dir: str | None = None,
    filename: str | None = None,
    format: str = "wav"
) -> str:
    """Start a background generation job and return job ID."""
    job_id = str(uuid.uuid4())[:8]

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

    # Create job record
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "queued",
            "message": "Job queued",
            "prompt": prompt,
            "duration": duration,
            "filename": filename,
            "format": format,
            "output_dir": str(out_dir),
            "created_at": datetime.now().isoformat(),
            "result": None
        }

    # Start background thread
    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, prompt, duration, out_dir, filename, format),
        daemon=True
    )
    thread.start()

    return job_id


def get_job_status(job_id: str) -> dict | None:
    """Get the status of a generation job."""
    with _jobs_lock:
        return _jobs.get(job_id, None)


def list_jobs() -> list[dict]:
    """List all jobs."""
    with _jobs_lock:
        return [
            {"job_id": jid, **{k: v for k, v in job.items() if k != "result"}}
            for jid, job in _jobs.items()
        ]


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

This starts a background generation job and returns a job_id. Use check_generation_status to poll for completion.

Best for: environmental sounds, foley, game sound effects, ambient audio.

Example prompts:
- "arcade game explosion, 8-bit style, retro"
- "whoosh sound, fast object passing by"
- "dark ambient tension drone, synth pad, ominous"
- "glass breaking, shatter"
- "footsteps on wooden floor"

Tips:
- Be specific and descriptive
- Include style keywords (retro, 8-bit, cinematic, realistic)
- Duration: 1-30 seconds (5s default)
- Generation takes ~12s per 1s of audio on Apple Silicon
- After calling this, use check_generation_status with the returned job_id""",
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
            name="check_generation_status",
            description="""Check the status of a sound generation job.

Returns the current status: queued, loading_model, generating, saving, completed, or failed.
When completed, includes the result with file_path.

Poll this every few seconds after calling generate_sound_effect.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The job ID returned by generate_sound_effect"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="list_generation_jobs",
            description="List all generation jobs and their current status.",
            inputSchema={
                "type": "object",
                "properties": {}
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
            job_id = start_generation(
                prompt=arguments["prompt"],
                duration=arguments.get("duration", 5.0),
                output_dir=arguments.get("output_dir"),
                filename=arguments.get("filename"),
                format=arguments.get("format", "wav")
            )

            duration = min(30.0, max(1.0, arguments.get("duration", 5.0)))
            estimated_time = int(duration * 12)  # ~12s per 1s of audio

            return [TextContent(type="text", text=json.dumps({
                "job_id": job_id,
                "status": "queued",
                "message": f"Generation started. Estimated time: ~{estimated_time}s. Use check_generation_status with job_id '{job_id}' to poll for completion."
            }, indent=2))]
        except Exception as e:
            logger.exception("Error starting generation")
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))]

    elif name == "check_generation_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text=json.dumps({
                "error": "job_id is required"
            }, indent=2))]

        job = get_job_status(job_id)
        if job is None:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Job '{job_id}' not found"
            }, indent=2))]

        response = {
            "job_id": job_id,
            "status": job["status"],
            "message": job["message"],
            "prompt": job["prompt"],
            "duration": job["duration"],
        }

        if job["status"] == "completed" and job.get("result"):
            response["result"] = job["result"]
        elif job["status"] == "failed" and job.get("result"):
            response["error"] = job["result"].get("error")

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    elif name == "list_generation_jobs":
        jobs = list_jobs()
        return [TextContent(type="text", text=json.dumps({
            "count": len(jobs),
            "jobs": jobs
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
            "active_jobs": len([j for j in _jobs.values() if j["status"] not in ("completed", "failed")])
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
