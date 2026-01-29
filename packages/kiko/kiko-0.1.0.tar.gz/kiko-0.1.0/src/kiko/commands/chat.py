"""Chat-focused commands."""

from typing import Any

from kiko.app import app
from kiko.runtime.context import Context
from kiko.ui import components


@app.command(
    name='say',
    help='Say a message',
    category='chat',
    usage='/say <message>',
    example='/say hello',
)
def say(ctx: Context, args: list[Any]):
    """Store a message and render it to the console."""
    text = ' '.join(args)

    # 1. Runtime + Output: store message and render panel
    panel = components.render_message(role='user', text=text)
    ctx.emit('user', text, render=panel)
