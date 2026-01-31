from bluer_sbc.README.design import design_doc_parts

parts = {
    "dupont-cables": "1 x 30 cm + 1 x 10 cm",
    "numpad": "",
    "nuts-bolts-spacers": " + ".join(
        [
            "M2: ({})".format(
                " + ".join(
                    [
                        "2 x bolt",
                        "4 x nut",
                        "2 x 5 mm spacer",
                    ]
                )
            ),
            "M3: ({})".format(
                " + ".join(
                    [
                        "4 x 15 mm spacer",
                    ]
                )
            ),
        ]
    ),
    "rpi": "",
    "rpi-camera": "",
    "sd-card-32-gb": "",
    "strong-thread": "1 m",
    "swallow-shield": "",
    "ultrasonic-sensor": "4 x",
    "XL4015": "",
}


docs = [
    {
        "path": "../docs/swallow-head/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="../parts",
        ),
    }
]
