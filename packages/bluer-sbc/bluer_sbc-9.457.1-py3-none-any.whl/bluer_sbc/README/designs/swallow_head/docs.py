from bluer_sbc.README.designs.swallow_head import body, parts
from bluer_sbc.README.designs.swallow_head.items import items


docs = (
    [
        {
            "path": "../docs/swallow-head",
            "items": items,
        }
    ]
    + parts.docs
    + body.docs
)
