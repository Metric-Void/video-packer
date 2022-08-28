from . import values as v

presets_dict = {
    "TL 4K": {
        "encoding": v.vencoding["h265"],
        "vcodec": v.vcodec["nvenc"],
        "acodec": v.acodec["aac"],
        "format": v.format["mp4"],
        "rc": v.rc["vbr"],
        "param1": "10M",
        "param2": "15M"
    },
    "TL 1080p": {
        "encoding": v.vencoding["h265"],
        "vcodec": v.vcodec["nvenc"],
        "acodec": v.acodec["aac"],
        "format": v.format["mp4"],
        "rc": v.rc["vbr"],
        "param1": "5M",
        "param2": "10M"
    }
}
