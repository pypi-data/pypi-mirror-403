from bluer_objects.README.alias import list_of_aliases

from bluer_ai import NAME
from bluer_ai.README import aliases


docs = [
    {
        "path": "../..",
        "macros": {
            "aliases:::": list_of_aliases(NAME),
        },
    },
    {
        "path": "../docs",
    },
] + aliases.docs
