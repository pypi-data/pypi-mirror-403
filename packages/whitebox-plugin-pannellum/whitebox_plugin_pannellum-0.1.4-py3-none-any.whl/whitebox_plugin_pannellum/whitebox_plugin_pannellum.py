import whitebox


class WhiteboxPluginPannellum(whitebox.Plugin):
    name = "Pannellum"

    exposed_component_map = {
        "ui": {
            "video360": "Pannellum360Video",
        }
    }


plugin_class = WhiteboxPluginPannellum
