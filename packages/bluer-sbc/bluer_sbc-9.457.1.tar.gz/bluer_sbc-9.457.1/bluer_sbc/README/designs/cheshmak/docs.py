from bluer_sbc.README.designs.cheshmak import (
    install,
    operation,
    parts,
    terraform,
    validations,
)
from bluer_sbc.README.designs.cheshmak.items import items
from bluer_sbc.README.designs.cheshmak.body import docs as body


docs = (
    [
        {
            "path": "../docs/cheshmak",
            "items": items,
        }
    ]
    + body.docs
    + install.docs
    + operation.docs
    + parts.docs
    + terraform.docs
    + validations.docs
)
