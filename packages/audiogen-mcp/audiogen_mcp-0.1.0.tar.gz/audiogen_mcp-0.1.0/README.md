# AudioGen MCP Server

[![PyPI version](https://badge.fury.io/py/audiogen-mcp.svg)](https://badge.fury.io/py/audiogen-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP server that generates sound effects from text descriptions using Meta's AudioGen model. Designed for Apple Silicon Macs.

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.9-3.11 (3.12 not yet supported by audiocraft)
- ffmpeg: `brew install ffmpeg`
- ~4GB disk space for model weights
- ~8GB RAM recommended

## Installation

```bash
uvx audiogen-mcp
```

That's it. The first run will download the AudioGen model (~2GB), which takes about 2 minutes.

## Configure Claude Code

### Option 1: CLI (Recommended)

```bash
claude mcp add audiogen uvx -- audiogen-mcp
```

### Option 2: Manual JSON Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audiogen": {
      "command": "uvx",
      "args": ["audiogen-mcp"]
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
