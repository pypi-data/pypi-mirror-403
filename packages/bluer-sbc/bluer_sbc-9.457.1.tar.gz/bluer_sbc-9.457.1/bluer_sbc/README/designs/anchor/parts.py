from bluer_sbc.README.design import design_doc_parts

parts = {
    "16-awg-wire": "40 cm x (red + black/blue)",
    "dc-switch": "",
    "connector": "1 female",
    "keyboard": "",
    "nuts-bolts-spacers": " + ".join(
        [
            "M2.5: ({})".format(
                " + ".join(
                    [
                        "4 x bolt",
                        "4 x nut",
                        "8 x 10 mm spacer",
                    ]
                )
            ),
            "M3: ({})".format(
                " + ".join(
                    [
                        "1 x bolt",
                        "5 x nut",
                        "4 x 5 mm spacer",
                        "4 x 15 mm spacer",
                        "5 x 25 mm spacer",
                    ]
                )
            ),
        ]
    ),
    "PCB-single-14x9_5": "",
    "plexiglass": "14 cm x 9.5 cm",
    "rpi": "",
    "sd-card-32-gb": "",
    "solid-cable-1-15": "10 cm x (red + black/blue)",
    "swallow-shield": "",
    "XL4015": "",
    "sx1276": "",
    "whip-antenna": "",
}

docs = [
    {
        "path": "../docs/anchor/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
