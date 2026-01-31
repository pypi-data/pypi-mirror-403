from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.swallow_head import image_template
from bluer_sbc.README.designs.swallow_head import latest_version

items = ImageItems(
    {
        image_template(latest_version).format(f"{index+1:02}.jpg"): ""
        for index in range(6)
    }
)
