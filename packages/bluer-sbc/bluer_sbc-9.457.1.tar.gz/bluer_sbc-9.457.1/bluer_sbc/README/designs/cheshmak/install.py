from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.cheshmak import image_template

docs = [
    {
        "path": "../docs/cheshmak/install.md",
        "items": ImageItems(
            {
                image_template.format("IMG_20260126_192557.jpg"): "",
            }
        ),
    },
]
