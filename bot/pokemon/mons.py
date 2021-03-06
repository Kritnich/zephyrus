import json
import random
from pokemon.moves import *
from re import sub
from typing import Union
from pyquery import PyQuery
from math import floor


class Form:
    def __init__(self, hp: int, atk: int, dfn: int, spa: int, spd: int, spe: int, type1, type2,
                 height: float, weight: float, name: str = ""):
        self.hp = hp
        self.atk = atk
        self.dfn = dfn
        self.spa = spa
        self.spd = spd
        self.spe = spe
        self.type1 = type1
        self.type2 = type2
        self.height = height
        self.weight = weight
        self.name = name

    @property
    def json(self):
        return [self.hp, self.atk, self.dfn, self.spa, self.spd, self.spe, self.type1, self.type2, self.height,
                self.weight, self.name]


formes = ["Attack", "Defense", "Speed", "Altered", "Origin", "Land", "Sky", "Incarnate", "Therian", "Aria",
          "Pirouette", "Blade", "Shield", "10%", "50%", "Complete"]
formAts = {
    "Mega": "Mega {}",
    "Mega X": "Mega {} X",
    "Mega Y": "Mega {} Y",
    "Alolan": "Alolan {}",
    "Black": "Black {}",
    "White": "White {}",
    "Ash": "Ash-{}",
    "Confined": "{} Confined",
    "Unbound": "{} Unbound",
    "Dusk Mane": "Dusk Mane {}",
    "Dawn Wings": "Dawn Wings {}",
    "Ultra": "Ultra {}",
    "Red-Striped": "Red-Striped {}",
    "Blue-Striped": "Blue-Striped {}"
}


class Species:
    def __init__(self, name, *forms: Form):
        self.name = name
        self.forms = {g.name: g for g in forms}

    def get_form_name(self, s: str):
        if not s:
            return list(self.forms)[0]
        for g in self.forms:
            if fix(g) == fix(s):
                return g
        else:
            raise ValueError("Form not found.")

    @property
    def json(self):
        return [self.name, *[g.json for g in self.forms.values()]]


natures = [
    'Hardy', 'Lonely', 'Adamant', 'Naughty', 'Brave',
    'Bold', 'Docile', 'Impish', 'Lax', 'Relaxed',
    'Modest', 'Mild', 'Bashful', 'Rash', 'Quiet',
    'Calm', 'Gentle', 'Careful', 'Quirky', 'Sassy',
    'Timid', 'Hasty', 'Jolly', 'Naive', 'Serious'
]


class Mon:
    """The wieldiest of unwieldy classes."""

    def __init__(self, spc: Union[Species, str], **kwargs):
        self.nickname = kwargs.get("nickname", None)
        if isinstance(spc, str):
            self.species = natDex[spc]
        else:
            self.species = spc
        self.givenForm = kwargs.get("form", "")
        self.form = self.species.forms[self.species.get_form_name(self.givenForm)]
        self.type1 = self.form.type1  # need to be changeable bc of moves like Soak
        self.type2 = self.form.type2
        self.level = kwargs.get("level", kwargs.get("lvl", 100))
        self.nature = kwargs.get("nature", "Hardy")
        self.iv = kwargs.get("iv", [0, 0, 0, 0, 0, 0])
        self.ev = kwargs.get("ev", [0, 0, 0, 0, 0, 0])
        self.stat_stages = kwargs.get(
            "stat_stages", {"atk": 0, "dfn": 0, "spa": 0, "spd": 0, "spe": 0, "eva": 0, "acc": 0}
        )
        self.hpc = self.hp - kwargs.get("dmg", 0)
        self.status_condition = kwargs.get("status_condition", None)
        self.stat_con_time = kwargs.get("sct", 0)
        self.confused = kwargs.get("confused", False)
        self.confusion_time = kwargs.get("confusion_time", 0) if self.confused else 0

    @property
    def dex_no(self):
        return list(natDex).index(self.species.name) + 1

    @property
    def generation(self):
        return [g for g in range(8) if self.dex_no <= generationBounds[g]][-1]

    @property
    def bulbapedia(self):
        return f"https://bulbapedia.bulbagarden.net/wiki/{'_'.join(self.species.name.split())}_(Pok\u00e9mon\\)"

    @property
    def serebii(self):
        return f"https://serebii.net/pokedex-sm/{self.dex_no}.shtml"

    @property
    def pokemondb(self):
        return f"https://pokemondb.net/pokedex/{fix(self.species.name)}"

    @property
    def form_names(self):
        return [Mon(self.species, form=g).full_name for g in natDex[self.species.name].forms]

    @property
    def types(self):
        return tuple(g for g in [self.type1, self.type2] if g)

    @property
    def base_stats(self):
        return self.form.hp, self.form.atk, self.form.dfn, self.form.spa, self.form.spd, self.form.spe

    @property
    def height(self):
        return self.form.height

    @property
    def weight(self):
        return self.form.weight

    @property
    def name(self):
        return self.nickname if self.nickname else self.full_name

    @property
    def full_name(self):
        if not self.form.name:
            return self.species.name
        if self.form.name in formes:
            return f"{self.species.name} ({self.form.name} Forme)"
        elif self.species.name == "Vivillon":
            return f"{self.species.name} ({self.form.name} Pattern)"
        elif self.species.name in ["Flabébé", "Floette", "Florges"]:
            return f"{self.species.name} ({self.form.name} Flower)"
        elif self.species.name == "Oricorio":
            return f"{self.species.name} ({self.form.name} Style)"
        elif self.species.name in ["Pumpkaboo", "Gourgeist"]:
            return f"{self.form.name} Size {self.species.name}"
        elif self.species.name == "Wormadam":
            return f"{self.form.name} Cloak {self.species.name}"
        elif self.species.name in ["Silvally", "Arceus"]:
            return f"{self.species.name} ({self.form.name}-type)"
        elif self.species.name == "Furfrou":
            return f"{self.species.name} ({self.form.name} Trim)"
        return formAts.get(self.form.name, "{} (" + self.form.name + " Form)").format(self.species.name)

    @property
    def ni(self):
        return natures.index(self.nature)

    def stat_level(self, stat):
        n = 3 if stat in ["eva", "acc"] else 2
        change = self.stat_stages[stat]
        return (n + (0 if change <= 0 else change)) / (n - (0 if change >= 0 else change))

    @property
    def hp(self):
        """Maximum HP; current HP is ``Mon.hpc``"""
        return floor((2 * self.form.hp + self.iv[0] + floor(self.ev[0] / 4)) * self.level / 100) + self.level + 10

    @property
    def atk_base(self):
        return floor(
            (floor((2 * self.form.atk + self.iv[1] + floor(self.ev[1] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.ni // 5 == 0) - 0.1 * (self.ni % 5 == 0))
        )

    @property
    def atk(self):
        return self.atk_base * self.stat_level("atk")

    @property
    def dfn_base(self):
        return floor(
            (floor((2 * self.form.dfn + self.iv[2] + floor(self.ev[2] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.ni // 5 == 1) - 0.1 * (self.ni % 5 == 1))
        )

    @property
    def dfn(self):
        return self.dfn_base * self.stat_level("dfn")

    @property
    def spa_base(self):
        return floor(
            (floor((2 * self.form.spa + self.iv[3] + floor(self.ev[3] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.ni // 5 == 2) - 0.1 * (self.ni % 5 == 2))
        )

    @property
    def spa(self):
        return self.spa_base * self.stat_level("spa")

    @property
    def spd_base(self):
        return floor(
            (floor((2 * self.form.spd + self.iv[4] + floor(self.ev[4] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.ni // 5 == 3) - 0.1 * (self.ni % 5 == 3))
        )

    @property
    def spd(self):
        return self.spd_base * self.stat_level("spd")

    @property
    def spe_base(self):
        return floor(
            (floor((2 * self.form.spe + self.iv[5] + floor(self.ev[5] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.ni // 5 == 4) - 0.1 * (self.ni % 5 == 4))
        )

    @property
    def spe(self):
        return self.spe_base * self.stat_level("spe") * (0.5 if self.status_condition == paralyzed else 1)

    @property
    def eva(self):
        return self.stat_level("eva")

    @property
    def acc(self):
        return self.stat_level("acc")

    def eff(self, typ: str):
        return effectiveness[typ].get(self.type1, 1) * effectiveness[typ].get(self.type2, 1)

    def apply(self, stat: Union[StatChange, StatusEffect]):
        ret = {}
        if random.random() < stat.chance:
            if isinstance(stat, StatChange):
                for k, v in stat.stages.items():
                    change = max(-6, min(6, self.stat_stages[k] + v)) - self.stat_stages[k]
                    self.stat_stages[k] += change
                    ret[k] = -20 if not change and v < 1 else change  # -20 is arbitrary, just to distinguish from -0
            else:
                if not self.status_condition:
                    self.status_condition = stat.effect
                    self.stat_con_time = random.randrange(1, 4)
        return ret


with open("stats.json" if __name__ == "__main__" else "pokemon/stats.json", "r") as file:
    natDex = {g: Species(j[0], *[Form(*k) for k in j[1:]]) for g, j in json.load(file).items()}


with open("dex.json" if __name__ == "__main__" else "pokemon/dex.json", "r") as file:
    dexEntries = json.load(file)


with open("species.json" if __name__ == "__main__" else "pokemon/species.json", "r") as file:
    species = json.load(file)


with open("eff.json" if __name__ == "__main__" else "pokemon/eff.json", "r") as file:
    effectiveness = json.load(file)


def fix(s: str, joiner: str = "-"):
    return sub(f"{joiner}+", joiner, sub(f"[^a-z0-9{joiner}]+", "", sub(r"\s+", joiner, s.lower().replace("é", "e"))))


fixedDex = {fix(g): g for g in natDex}


def read_url(url: str):
    return str(PyQuery(url, {'title': 'CSS', 'printable': 'yes'}))


imgLink = "https://img.pokemondb.net/artwork/vector/{}.png"
dexLink = "https://pokemondb.net/pokedex/{}"
generationBounds = [0, 151, 251, 386, 493, 649, 721, 809]
gameGenerations = {
    "Red": 1, "Blue": 1, "Yellow": 1, "Gold": 2, "Silver": 2, "Crystal": 2, "Ruby": 3, "Sapphire": 3, "Emerald": 3,
    "FireRed": 3, "LeafGreen": 3, "Diamond": 4, "Pearl": 4, "Platinum": 4, "HeartGold": 4, "SoulSilver": 4,
    "Black": 5, "White": 5, "Black 2": 5, "White 2": 5, "X": 6, "Y": 6, "Omega Ruby": 6, "Alpha Sapphire": 6,
    "Sun": 7, "Moon": 7, "Ultra Sun": 7, "Ultra Moon": 7
}


class Dex:
    """Doesn't do much; just a way to access mons either by their name or dex number."""
    def __init__(self, name: str):
        self.name = name
        self.dex = {g: j for g, j in list(natDex.items())[:generationBounds[gameGenerations[name]]]}

    def __len__(self):
        return len(self.dex)

    def __getitem__(self, item: Union[int, str]):
        if isinstance(item, int):
            return self.dex[list(self.dex)[(item - 1) % len(self.dex)]]
        return self.dex[item]

    def __contains__(self, item):
        return item in self.dex


gameDexes = {g: Dex(g) for g in gameGenerations}


def image(m: Mon):
    if m.form.name:
        if m.species.name == "Minior" and m.form == "Core":
            suffix = "-" + random.choice(["orange", "yellow", "green", "blue", "indigo", "purple"]) + "-core"
        else:
            suffix = "-" + fix(m.form.name)
    else:
        suffix = ""
    return imgLink.format(fix(m.species.name) + suffix)


def stat_change_text(mon: Mon, stat: str, change: int):
    ret = "{name}'s {stat} won't go any lower!" if change == -20 else \
        StatChange.modifier_strings[max(-3, min(3, change))]
    return ret.format(name=mon.name, stat=StatChange.stat_name_dict[stat])


exemplaryMons = {}
for sp in natDex.values():
    assert isinstance(sp, Species)
    if sp.name not in ["Arceus", "Silvally", "Meltan", "Melmetal"]:
        for form in sp.forms.values():
            exemplaryMons[frozenset([form.type1, form.type2])] = \
                exemplaryMons.get(frozenset([form.type1, form.type2]), []) + [f"{sp.name} {form.name}".strip()]
