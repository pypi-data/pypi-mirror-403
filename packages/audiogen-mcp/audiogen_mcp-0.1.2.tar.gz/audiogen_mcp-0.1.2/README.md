# AudioGen MCP Server

[![PyPI version](https://badge.fury.io/py/audiogen-mcp.svg)](https://badge.fury.io/py/audiogen-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP server that generates sound effects from text descriptions using Meta's AudioGen model. Designed for Apple Silicon Macs.

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.9-3.11 (3.12+ not yet supported by audiocraft)
- ffmpeg: `brew install ffmpeg`
- ~4GB disk space for model weights
- ~8GB RAM recommended

## Installation

Due to audiocraft's complex dependencies, installation requires a virtual environment:

```bash
# Create virtual environment with Python 3.11
uv venv ~/.audiogen-env --python 3.11
source ~/.audiogen-env/bin/activate

# Install dependencies
uv pip install torch torchaudio

# Install audiocraft (may take a few minutes to build)
uv pip install audiocraft --no-build-isolation

# Install audiogen-mcp
uv pip install audiogen-mcp
```

The first run will download the AudioGen model (~2GB).

## Configure Claude Code

```bash
claude mcp add audiogen ~/.audiogen-env/bin/python -- -m audiogen_mcp.server
```

Or add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audiogen": {
      "command": "/Users/YOUR_USERNAME/.audiogen-env/bin/python",
      "args": ["-m", "audiogen_mcp.server"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `generate_sound_effect` | Generate a single sound effect from text |
| `generate_batch_sound_effects` | Generate multiple sounds at once |
| `list_generated_sounds` | List previously generated files |
| `get_model_status` | Check model and device status |

## Example Prompts

Once configured, ask Claude Code to generate sounds:

- "Generate an explosion sound effect"
- "Create UI sounds: click, hover, and error"
- "Make a retro 8-bit power-up sound, 2 seconds long"
- "Generate footsteps on gravel, 5 seconds"

### Prompt Tips

For best results, be specific:

```
# Good
"glass breaking, single wine glass falling on tile floor"
"8-bit arcade explosion, retro game style"
"button click, soft, satisfying UI sound"

# Less good
"glass sound"
"explosion"
"click"
```

Include style, mood, and context for better results.

## Performance

- ~60 seconds to generate 5 seconds of audio
- First generation takes longer (model loading)
- Uses Metal Performance Shaders (MPS) for GPU acceleration

## Output

Generated files save to `~/audiogen_outputs/` by default as WAV files.

## Troubleshooting

### Installation fails with xformers error

This is expected on Apple Silicon. The server mocks xformers at runtime since it's only needed for CUDA. If audiocraft installation fails, try:

```bash
uv pip install torch torchaudio
uv pip install audiocraft --no-build-isolation
```

### Model download fails

Ensure stable internet and sufficient disk space. The model downloads from HuggingFace Hub.

### Slow generation

Check device with `get_model_status` tool. CPU fallback is 10-20x slower than MPS.

### MPS not available

Requires macOS 12.3+ and PyTorch 2.0+.

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- [Meta AudioCraft](https://github.com/facebookresearch/audiocraft) - The underlying AI model
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol specification
