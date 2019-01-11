import discord
import asyncio
from inspect import iscoroutinefunction
from discord.ext import commands
from typing import Union
from minigames.risk import snip
from math import ceil


User = Union[discord.Member, discord.User]
MR = Union[discord.Message, discord.Reaction]
Flint = Union[float, int]


class Zeph(commands.Bot):
    def __init__(self):
        super().__init__("z!", case_insensitive=True)
        del self.all_commands["help"]

    @property
    def emojis(self):
        return {g.name: g for g in self._connection.emojis}

    @property
    def strings(self):
        return {g: str(j) for g, j in self.emojis.items()}


zeph = Zeph()


@zeph.event
async def on_message(message: discord.Message):
    zeph.dispatch("reaction_or_message", message, message.author)
    await zeph.process_commands(message)


@zeph.event
async def on_reaction_add(reaction: discord.Reaction, user: User):
    zeph.dispatch("reaction_or_message", reaction, user)


def hexcol(hex_code: str):
    if int(hex_code, 16) < 0:
        raise ValueError("negative hexcol code")
    if int(hex_code, 16) > 16777215:
        raise ValueError("hexcol int should be less than 16777215")
    return discord.Colour(int(hex_code, 16))


class IL:
    def __init__(self, obj):
        self.object = obj

    def __str__(self):
        return str(self.object)


class EmbedAuthor:
    def __init__(self, name, url=discord.Embed.Empty, icon=discord.Embed.Empty):
        self.name = name
        self.url = url
        self.icon = icon


def author_from_user(user: User, name: str=None, url: str=discord.Embed.Empty):
    return EmbedAuthor(name if name else f"{user.name}#{user.discriminator}", icon=user.avatar_url, url=url)


# INLINE: IF TRUE, PUTS IN SAME LINE. IF FALSE, PUTS ON NEW LINE.
def construct_embed(**kwargs):
    title = kwargs.get("s", kwargs.get("title", discord.embeds.EmptyEmbed))
    desc = kwargs.get("d", kwargs.get("desc", discord.embeds.EmptyEmbed))
    color = kwargs.get("col", kwargs.get("color", discord.embeds.EmptyEmbed))
    fields = kwargs.get("fs", kwargs.get("fields", {}))
    ret = discord.Embed(title=title, description=desc, colour=color)
    for i in fields:
        if len(str(fields[i])) != 0:
            ret.add_field(name=i, value=str(fields[i]),
                          inline=(False if type(fields[i]) == IL else
                                  kwargs.get("same_line", False)))
    if kwargs.get("footer"):
        ret.set_footer(text=kwargs.get("footer"))
    if kwargs.get("thumb", kwargs.get("thumbnail")):
        ret.set_thumbnail(url=kwargs.get("thumb", kwargs.get("thumbnail")))
    if kwargs.get("author"):
        ret.set_author(name=kwargs.get("author").name, url=kwargs.get("author").url, icon_url=kwargs.get("author").icon)
    if kwargs.get("url"):
        ret.url = kwargs.get("url")
    if kwargs.get("image"):
        ret.set_image(url=kwargs.get("image"))
    return ret


class Emol:  # fancy emote-color embeds
    def __init__(self, e: Union[discord.Emoji, str], col: discord.Colour):
        self.emoji = str(e)
        self.color = col

    def con(self, s: str=None, **kwargs):  # constructs
        return construct_embed(title=f"{self.emoji} \u2223 {s}" if s else None, col=self.color, **kwargs)

    async def send(self, destination: commands.Context, s: str=None, **kwargs):  # sends
        return await destination.send(embed=self.con(s, **kwargs))

    async def edit(self, message: discord.Message, s: str=None, **kwargs):  # edits message
        return await message.edit(embed=self.con(s, **kwargs))


class ClientEmol(Emol):
    def __init__(self, e: Union[discord.Emoji, str], col: discord.Colour, dest: commands.Context):
        super().__init__(e, col)
        self.dest = dest

    async def say(self, s: str=None, **kwargs):
        return await self.send(self.dest, s, **kwargs)


# IMPORTANT EMOLS
err = Emol(":no_entry:", hexcol("880000"))  # error
succ = Emol(":white_check_mark:", hexcol("22bb00"))  # success
chooseEmol = Emol(":8ball:", hexcol("e1e8ed"))
zhong = Emol(":u7a7a:", hexcol("8000b0"))
wiki = Emol(":globe_with_meridians:", hexcol("4100b5"))


async def confirm(s: str, dest: commands.Context, caller: User, **kwargs):
    def pred(r: discord.Reaction, u: User):
        return u == caller and r.emoji in [zeph.emojis["yes"], zeph.emojis["no"]] and r.message.id == message.id

    emol = kwargs.get("emol", Emol(zeph.emojis["yield"], hexcol("DD2E44")))

    message = await emol.send(dest, s, d=f"To {kwargs.get('yes', 'confirm')}, react with {zeph.emojis['yes']}. "
                                         f"To {kwargs.get('no', 'cancel')}, react with {zeph.emojis['no']}.")
    await message.add_reaction(zeph.emojis["yes"])
    await message.add_reaction(zeph.emojis["no"])
    try:
        con = (await zeph.wait_for("reaction_add", timeout=kwargs.get("timeout", 120), check=pred))[0]
    except asyncio.TimeoutError:
        await emol.edit(message, "Confirmation request timed out.")
        return False
    else:
        return con.emoji == zeph.emojis["yes"]


async def image_url(fp: str):
    return (await zeph.get_channel(528460450069872642).send(file=discord.File(fp))).attachments[0].url


def plural(s: str, n: Union[float, int], **kwargs):
    return kwargs.get("plural", s + "s") if n != 1 else s


def none_list(l: Union[list, tuple], joiner: str=", "):
    return joiner.join(l) if l else "none"


def flint(n: Flint):
    return int(n) if int(n) == n else n


class SigFig:
    def __init__(self, s: str, keep_non_dec: bool=False):
        if s[0] == "-":
            self.figStr = s[1:].split("e")[0]
            self.s = s[1:]
            self.negative = True
        else:
            self.figStr = s.split("e")[0]
            self.s = s
            self.negative = False
        try:
            float(s)
        except ValueError:
            raise commands.BadArgument
        self.keepNonDecimal = keep_non_dec

    @property
    def n(self):
        return float(self.add_negative(self.s))

    @property
    def figs(self):
        if self.n == 0:  # workaround for a value of zero with sig figs
            return SigFig(self.s.replace("0", "1")).figs
        if "." in self.figStr:
            return len("".join(self.figStr.split(".")).lstrip("0"))
        return len(self.figStr.rstrip("0"))

    def __str__(self):
        return self.add_negative(self.s)

    def __round__(self, n=None):
        if not n:
            return self.n
        if self.n == 0:  # zero workaround
            return str(round(SigFig(self.s.replace("0", "1")))).replace("1", "0")
        if n < self.figs:
            return self.add_negative(self.decrease_sf(n))
        else:
            return self.add_negative(self.increase_sf(n))

    def increase_sf(self, to: int):
        if to < len(str(int(self.n))):
            return self.s
        if to == len(str(int(self.n))):
            return self.s + ("." if str(int(self.n))[-1] == "0" else "")
        return self.s + ("" if "." in self.s else ".") + "0" * (to - self.figs)

    def decrease_sf(self, to: int):
        if abs(self.n) >= 1:
            first_fig = to
        else:
            if self.s[0] == "0":
                first_fig = len(self.s.split(".")[1]) - len(self.s.split(".")[1].lstrip("0")) + to + 1
            else:
                first_fig = -int(self.s.split("e")[1]) + to
        if self.keepNonDecimal:
            ret = str(round(self.n, max(first_fig - len(str(int(self.n))), 0)))
        else:
            ret = str(round(self.n, first_fig - len(str(int(self.n)))))
        if ret[-2:] == ".0":  # removing trailing 0 added in round()
            if SigFig(ret).figs == to + 1:  # if the trailing zero makes one too many sig figs
                if ret[-3] == "0":  # if the last zero is significant
                    return ret[:-1]  # keep the decimal point to show that zeroes are significant
                else:
                    return ret[:-2]  # otherwise don't
            elif SigFig(ret[:-1]).figs > to:  # if the trailing zero makes more than one too many sig figs
                return ret[:-2]  # cut the whole decimal out
        return round(SigFig(ret), to)  # add any extra zeroes that get cut off in round(self.n)

    def add_negative(self, s: str):
        return ("-" if (self.negative and s[0] != "-") else "") + s


def add_commas(n: Union[Flint, str]):
    n = str(n).split(".")
    if len(n[0]) < 5:
        return ".".join(n)
    n[0] = ",".join(snip(n[0], 3, True))
    return ".".join(n)


def gradient(from_hex: str, to_hex: str, value: float):
    from_value = 1 - value
    return hexcol(
        "".join([hex(int(int(from_hex[g:g+2], 16) * from_value + int(to_hex[g:g+2], 16) * value))[2:]
                 for g in range(0, 5, 2)])
    )


def page_list(l: list, per_page: int, page: int):  # assumes page number is between 1 and total pages
    return l[int(page) * per_page - per_page:int(page) * per_page]


class Navigator:  # intended as a parent class
    def __init__(self, emol: Emol, l: list, per: int, s: str, **kwargs):
        self.emol = emol
        self.table = l
        self.per = per
        self.page = 1
        self.pgs = ceil(len(self.table) / self.per)
        self.title = s
        self.message = None
        self.kwargs = kwargs
        self.funcs = {}

    @property
    def legal(self):
        return ["◀", "▶"] + list(self.funcs.keys())

    def post_process(self):  # runs on page change!
        pass

    @property
    def con(self):
        return self.emol.con(self.title.format(page=self.page, pgs=self.pgs),
                             d=none_list(page_list(self.table, self.per, self.page), "\n"), **self.kwargs)

    async def run(self, ctx: commands.Context):
        self.message = await ctx.channel.send(embed=self.con)
        for button in self.legal:
            await self.message.add_reaction(button)
        while True:
            try:
                emoji = (await zeph.wait_for(
                    'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
                    r.message.id == self.message.id and u == ctx.author
                ))[0].emoji
            except asyncio.TimeoutError:
                return
            if emoji in self.funcs:
                if iscoroutinefunction(self.funcs[emoji]):
                    await self.funcs[emoji]()
                else:
                    self.funcs[emoji]()
            try:
                self.page = (self.page + (-1 if emoji == "◀" else 1 if emoji == "▶" else 0) - 1) % self.pgs + 1
            except ZeroDivisionError:
                self.page = 1
            await self.message.edit(embed=self.con)
            try:
                await self.message.remove_reaction(emoji, ctx.author)
            except discord.errors.Forbidden:
                pass
            if iscoroutinefunction(self.post_process):
                await self.post_process()
            else:
                self.post_process()


def lower(l: Union[list, tuple]):
    if type(l) == tuple:
        return tuple(g.lower() for g in l)
    return [g.lower() for g in l]


blue = hexcol("5177ca")  # color that many commands use
