class PaginatedEmbed:
    def __init__(self, ctx, embeds):
        self.ctx = ctx
        self.embeds = embeds
        self.index = 0

    async def start(self):
        if not self.embeds:
            return

        message = await self.ctx.send(embed=self.embeds[self.index])
        await message.add_reaction('◀️')
        await message.add_reaction('▶️')

        def check(reaction, user):
            return user == self.ctx.author and str(reaction.emoji) in ['◀️', '▶️']

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except Exception as e:
                print(e)
                break

            if str(reaction.emoji) == '▶️' and self.index < len(self.embeds) - 1:
                self.index += 1
                await message.edit(embed=self.embeds[self.index])
            elif str(reaction.emoji) == '◀️' and self.index > 0:
                self.index -= 1
                await message.edit(embed=self.embeds[self.index])

            await message.remove_reaction(reaction, user)

        await message.clear_reactions()
