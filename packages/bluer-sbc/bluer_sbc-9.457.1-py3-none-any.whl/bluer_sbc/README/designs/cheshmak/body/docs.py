from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.cheshmak import image_template
from bluer_sbc.README.designs.cheshmak.body import v1, v2

docs = (
    [
        {
            "path": "../docs/cheshmak/body",
            "items": ImageItems(
                {
                    image_template.format("20260114_125949.jpg"): "",
                    image_template.format("20260114_130000.jpg"): "",
                    image_template.format("20260114_130005.jpg"): "",
                    image_template.format("20260114_130011.jpg"): "",
                    image_template.format("20260114_130016.jpg"): "",
                    image_template.format("20260114_130023.jpg"): "",
                }
            ),
        }
    ]
    + v1.docs
    + v2.docs
)
