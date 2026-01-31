import whitebox


class WhiteboxPluginVideoJS(whitebox.Plugin):
    name = "VideoJS"

    exposed_component_map = {
        "ui": {
            "video": "VideoJS",
        }
    }


plugin_class = WhiteboxPluginVideoJS
