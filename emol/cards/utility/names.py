from random import randint

"""
Simple name generator based on heraldic terms

Generates random name identifiers of the form "argent-base-charge"
"""

TINCTURES = [
    "or",
    "argent",
    "gules",
    "azure",
    "sable",
    "purpure",
    "vert",
    "vair",
    "ermine",
]

BEASTS = {
    1: [
        "antelope",
        "arrow",
        "attire",
        "ax",
        "bat",
        "bear",
        "bee",
        "bird",
        "boar",
        "bull",
        "cat",
        "chicken",
        "cock",
        "crab",
        "crane",
        "crow",
        "deer",
        "dog",
        "dolphin",
        "dove",
        "dragon",
        "duck",
        "eagle",
        "elephant",
        "falcon",
        "fish",
        "fox",
        "goat",
        "goose",
        "griffin",
        "hare",
        "hawk",
        "heron",
        "horse",
        "harpy",
        "hart",
        "hedgehog",
        "ibex",
        "jaguar",
        "jester",
        "kestrel",
        "leopard",
        "lion",
        "lynx",
        "marten",
        "moose",
        "otter",
        "owl",
        "panther",
        "parrot",
        "peacock",
        "pelican",
        "penguin",
        "pheasant",
        "pig",
        "pony",
        "rabbit",
        "ram",
        "rattlesnake",
        "raven",
        "seagull",
        "seahorse",
        "serpent",
        "sheep",
        "snake",
        "stag",
        "swallow",
        "swan",
        "tiger",
        "tortoise",
        "turtle",
        "unicorn",
        "weasel",
        "whale",
        "wolf",
        "wyvern",
        "yale",
    ],
    2: [
        "passant",
        "rampant",
        "couchant",
        "statant",
        "sejant",
        "salient",
        "courant",
        "dormant",
        "volant",
        "combatant",
        "regardant",
    ],
}

CHARGES = {
    1: [
        "barry",
        "bendy",
        "chevronny",
        "fretty",
        "lozengy",
        "chequy",
        "gironny",
        "paly",
        "quarterly",
        "vairy",
    ],
    2: [
        "annulet",
        "arrowhead",
        "axe",
        "balance",
        "ball",
        "billet",
        "boat",
        "book",
        "bordure",
        "bouquet",
        "bow",
        "branch",
        "buglehorn",
        "castle",
        "chain",
        "chevron",
        "chief",
        "cinquefoil",
        "clarion",
        "cloud",
        "column",
        "compass-star",
        "cornucopia",
        "coronet",
        "couch",
        "crescent",
        "cross",
        "crown",
        "cup",
        "dagger",
        "dice",
        "escarbuncle",
        "estoile",
        "fess",
        "fetterlock",
        "fleur-de-lys",
        "flint",
        "flower",
        "fret",
        "gauntlet",
        "goblet",
        "grapes",
        "harp",
        "helm",
        "helmet",
        "hexagon",
        "holly",
        "horn",
        "hourglass",
        "issuant",
        "ivy",
        "jar",
        "key",
        "knife",
        "label",
        "lamp",
        "lozenge",
        "lute",
        "lyre",
        "mace",
        "maunch",
        "mermaid",
        "millrind",
        "moon",
        "morion",
        "mullet",
        "nautilus-shell",
        "needle",
        "oak-leaf",
        "octagon",
        "octopus",
        "orle",
        "ostrich-feather",
        "otter's-head",
        "oyster",
        "palmer's-staff",
        "palm-tree",
        "paschal-lamb",
        "peanut",
        "pecten",
        "pedestal",
        "pentagram",
        "pierced-mullet",
        "pierced-star",
        "pike",
        "pine-cone",
        "pine-tree",
        "plate",
        "plum",
        "pomegranate",
        "portcullis",
        "primrose",
        "pullet",
        "pumpkin",
        "quatrefoil",
        "quill",
        "quiver",
        "rainbow",
        "rose",
        "roundel",
        "saddle",
        "scallop-shell",
        "scroll",
        "seax",
        "ship",
        "shuttle",
        "snail",
        "spade",
        "spur-rowel",
        "square",
        "star",
        "sun",
        "sun-in-splendor",
        "thistle",
        "thunderbolt",
        "tower",
        "trapezium",
        "trefoil",
        "trident",
        "trivet",
        "trowel",
        "trumpet",
        "tulip",
        "turret",
        "urn",
        "vase",
        "vol",
        "wheat",
        "wheel",
        "wing",
        "woodbine",
        "maul",
        "worm",
        "wreath",
        "yoke",
        "zule",
    ],
}


def generate_name():
    """
    Generate a random name

    Choose either a (beast + attitude + tincture) or (division + charge + tincture) set
    """
    name = ""

    source = CHARGES if randint(1, 100) > 50 else BEASTS
    first = source[1][randint(0, len(source[1]) - 1)]
    second = source[2][randint(0, len(source[2]) - 1)]
    tincture = TINCTURES[randint(0, len(TINCTURES) - 1)]

    return f"{first}-{second}-{tincture}"


if __name__ == "__main__":
    for i in range(50):
        print(generate_name())
