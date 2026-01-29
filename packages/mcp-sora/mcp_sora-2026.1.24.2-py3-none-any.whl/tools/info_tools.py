"""Informational tools for Sora API."""

from core.server import mcp


@mcp.tool()
async def sora_list_models() -> str:
    """List all available Sora models and their capabilities.

    Shows all available model versions with their limits, features, and
    recommended use cases. Use this to understand which model to choose
    for your video generation.

    Returns:
        Table of all models with their version, limits, and features.
    """
    return """Available Sora Models:

| Model        | Max Duration | Quality | Features                          |
|--------------|--------------|---------|-----------------------------------|
| sora-2       | 15 seconds   | Good    | Standard generation, cost-effective |
| sora-2-pro   | 25 seconds   | Best    | Longer videos, higher quality     |

Video Size Options:
| Size   | Description                    |
|--------|--------------------------------|
| small  | Lower resolution, faster       |
| large  | Higher resolution, recommended |

Video Orientation Options:
| Orientation | Aspect Ratio | Use Case                    |
|-------------|--------------|-----------------------------|
| landscape   | 16:9         | YouTube, presentations      |
| portrait    | 9:16         | TikTok, Instagram Stories   |
| square      | 1:1          | Instagram posts, thumbnails |

Duration Options:
| Duration | Models                    |
|----------|---------------------------|
| 10s      | sora-2, sora-2-pro       |
| 15s      | sora-2, sora-2-pro       |
| 25s      | sora-2-pro only          |

Recommended: Use 'sora-2' with 'large' size for most use cases.
Use 'sora-2-pro' when you need longer videos (25s) or highest quality.
"""


@mcp.tool()
async def sora_list_actions() -> str:
    """List all available Sora API actions and corresponding tools.

    Reference guide for what each action does and which tool to use.
    Helpful for understanding the full capabilities of the Sora MCP.

    Returns:
        Categorized list of all actions and their corresponding tools.
    """
    return """Available Sora Actions and Tools:

Video Generation:
- sora_generate_video: Create video from a text prompt
- sora_generate_video_from_image: Create video from reference images (Image-to-Video)
- sora_generate_video_with_character: Create video with a character from reference video
- sora_generate_video_async: Create video with callback notification

Task Management:
- sora_get_task: Check status of a single generation
- sora_get_tasks_batch: Check status of multiple generations

Information:
- sora_list_models: Show available models and their capabilities
- sora_list_actions: Show this action reference (you are here)

Workflow Examples:

1. Simple Video Generation:
   sora_generate_video(prompt) → sora_get_task(task_id)

2. Image-to-Video:
   sora_generate_video_from_image(prompt, image_urls) → sora_get_task(task_id)

3. Character-based Video:
   sora_generate_video_with_character(prompt, character_url) → sora_get_task(task_id)

4. Async with Callback:
   sora_generate_video_async(prompt, callback_url) → Wait for callback

Tips:
- Video generation takes 1-2 minutes on average
- Use async generation with callbacks for production workflows
- sora-2-pro is required for 25-second videos
- Character videos cannot use real people, only animated characters
"""
