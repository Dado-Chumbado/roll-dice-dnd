

# Define a setup function to add commands
def commands_debug(bot):
    @bot.command(name="ping")
    async def ping(context):
        latency_ms = bot.latency * 1000  # Convert from seconds to ms
        await context.send(f"Pong {context.author.nick} - {latency_ms:.2f} ms")