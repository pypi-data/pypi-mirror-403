title:::

> anchor ⚓️ is a stationary rpi equipped with [LoRa](https://github.com/kamangir/bluer-algo/tree/main/bluer_algo/docs/lora-keyboard.md) transmission and either a GNSS receiver or a manually assigned position. It participates in [bps](https://github.com/kamangir/bluer-algo/tree/main/bluer_algo/docs/bps) as an anchor and simultaneously serves as [a remote keyboard interface](https://github.com/kamangir/bluer-algo/tree/main/bluer_algo/docs/lora-keyboard.md) for all [swallow](https://github.com/kamangir/bluer-ugv/tree/main/bluer_ugv/docs/swallow)s. Each swallow carries a LoRa receiver, listens to the anchor’s broadcast stream, and applies only the commands addressed to its own ID. BLE on each rpi operates independently and without interference, making this architecture a reliable, low-bandwidth, long-range control and reference system that scales from one robot to many.

anchor is a [swallow-head](../swallow-head) without the ultrasonic sensors and the camera.

- [parts](./parts.md)
- [body](./body)
- [terraform](./terraform.md)

items:::