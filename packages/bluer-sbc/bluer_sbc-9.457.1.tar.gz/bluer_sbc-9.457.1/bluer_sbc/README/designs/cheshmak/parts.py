from bluer_sbc.README.design import design_doc_parts

parts = {
    "16-awg-wire": "20 cm x (red + black/blue)",
    "dc-power-plug": "",
    "dc-switch": "",
    "gen1-s-blue-bracket": "",
    "hdmi-cable": "",
    "keyboard": "",
    "micro-hdmi-adapter": "",
    "nuts-bolts-spacers": ", ".join(
        [
            "M2.5: ({})".format(
                " + ".join(
                    [
                        "4 x bolt",
                        "4 x nut",
                        "12 x 10 mm spacer",
                    ]
                )
            ),
            "M3: ({})".format(
                " + ".join(
                    [
                        "4 x bolt",
                        "5 x nut",
                        "4 x 15 mm spacer",
                        "5 x 25 mm spacer",
                    ]
                )
            ),
        ]
    ),
    "PCB-single-14x9_5": "",
    "plexiglass": "14 cm x 9.5 cm",
    "power-adapter": "12 V DC, 5 A",
    "rpi": "",
    "swallow-shield": "",
    "XL4015": "",
}


docs = [
    {
        "path": "../docs/cheshmak/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
