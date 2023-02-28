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
    "sanguine",
    "murrey",
    "tenne",
    "vair",
    "ermine",
    "ermines",
    "erminois",
    "pean",
    "counter-ermine",
    "potent",
]

charges = [
    "angel",
    "antelope",
    "bear",
    "beast",
    "bird",
    "boar",
    "bull",
    "camel",
    "cat",
    "centaur",
    "cock",
    "crab",
    "crane",
    "crocodile",
    "deer",
    "dragon",
    "eagle",
    "elephant",
    "fox",
    "goat",
    "griffin",
    "hippopotamus",
    "horse",
    "hound",
    "jaguar",
    "lion",
    "lynx",
    "monkey",
    "monster",
    "mule",
    "otter",
    "panther",
    "pegasus",
    "pelican",
    "pig",
    "rabbit",
    "ram",
    "roc",
    "salamander",
    "seahorse",
    "serpent",
    "stag",
    "swan",
    "unicorn",
    "wolf",
]

subordinaries_and_birds = [
    "Martlet",
    "Fleur-de-lis",
    "Mullet",
    "Rose",
    "Thistle",
    "Trefoil",
    "bordure",
    "chief",
    "fess",
    "pale",
    "quarter",
    "bend",
    "cross",
    "saltire",
    "pile",
    "chevron",
    "flaunch",
    "gore",
    "gyron",
    "lozenge",
    "mascle",
    "mullet",
    "roundel",
    "annulet",
    "bezant",
    "cinquefoil",
    "leopard",
    "lion",
    "eagle",
    "falcon",
    "griffin",
    "harpy",
    "owl",
    "pelican",
    "raven",
    "vulture",
    "wyvern",
    "dragon",
    "griffin-segreant",
    "unicorn",
    "mermaid",
    "merman",
    "basilisk",
    "cockatrice",
    "wyvern-passant",
    "lion-rampant",
    "lion-passant",
    "lion-couchant",
    "lion-statant",
    "lion-gardant",
    "eagle-displayed",
    "eagle-rising",
    "eagle-volant",
]


WORDS = [
    "annulet",
    "argent",
    "bar",
    "barbed",
    "barry",
    "basilisk",
    "bezant",
    "billet",
    "bottony",
    "cabossed",
    "cadency",
    "canting",
    "canton",
    "charge",
    "chevron",
    "chief",
    "cinquefoil",
    "conjoined",
    "cotised",
    "couchant",
    "counter-change",
    "counter-compony",
    "couped",
    "courant",
    "crescent",
    "crest",
    "crosses",
    "cross-crosslet",
    "cross-flory",
    "cross-moline",
    "cross-paty",
    "tau-cross",
    "crusily",
    "dancetty",
    "dexter",
    "diaper",
    "differencing",
    "embattled",
    "engrailed",
    "ensign",
    "en-soleil",
    "erased",
    "erect",
    "ermine",
    "escallop",
    "escutcheon",
    "estoille",
    "fess",
    "fess-point",
    "field",
    "fitchy",
    "fleur-de-lis",
    "fleury",
    "flory",
    "foliated",
    "fret",
    "fretty",
    "fusil",
    "garb",
    "gorget",
    "griffin",
    "guardant",
    "gules",
    "gyron",
    "gyronny",
    "hauriant",
    "helm",
    "impaled",
    "in-bend",
    "indented",
    "in-fess",
    "in-orle",
    "in-pale",
    "invected",
    "jessant",
    "label",
    "langued",
    "lozenge",
    "lozengy",
    "luce",
    "mantling",
    "marshalling",
    "martlet",
    "mascle",
    "maunch",
    "membered",
    "mullet",
    "naiant",
    "nebuly",
    "nimbus",
    "octofoil",
    "ogress",
    "or",
    "ordinaries",
    "orle",
    "pale",
    "pall",
    "pallet",
    "party",
    "passant",
    "paty",
    "pellet",
    "per-bend",
    "per-chevron",
    "per-fess",
    "per-pale",
    "per-saltire",
    "pheon",
    "pierced",
    "pile",
    "plate",
    "proper",
    "purpure",
    "quarterly",
    "quatrefoil",
    "queue-fourche",
    "raguly",
    "rampant",
    "roundel",
    "sable",
    "salient",
    "saltire",
    "scallop",
    "seeded",
    "segreant",
    "semee",
    "sinister",
    "sixfoil",
    "slipped",
    "statant",
    "sun",
    "talbot",
    "tau",
    "tincture",
    "torteau",
    "trefoil",
    "trippant",
    "tun",
    "undy",
    "vair",
    "vert",
    "vested",
    "volant",
    "water-bouget",
    "wavy",
    "wreath",
    "wyvern",
]


def generate_name(length=3):
    """
    Generate a random name

    Will choose elements from the WORDS list and string them together
    separated by - characters. Will reject names that exceed `length`

    args:
        length - the maximum number of words in the generated name (default 3)
    """
    name_length = 0
    name = ""

    while True:
        element = WORDS[randint(0, len(WORDS) - 1)]
        element_length = len(element.split("-"))

        if name_length + element_length > length:
            continue

        name += element
        name_length = len(name.split("-"))
        if name_length >= length:
            return name

        name += "-"


if __name__ == "__main__":
    for i in range(50):
        print(generate_name())

    print(len(WORDS))
