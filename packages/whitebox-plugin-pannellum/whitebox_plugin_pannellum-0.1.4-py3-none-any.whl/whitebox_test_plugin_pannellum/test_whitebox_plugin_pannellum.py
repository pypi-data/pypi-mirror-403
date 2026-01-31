from django.test import TestCase
from plugin.manager import plugin_manager


class TestWhiteboxPluginPannellum(TestCase):
    def setUp(self):
        self.plugin = next(
            (
                x
                for x in plugin_manager.whitebox_plugins
                if x.__class__.__name__ == "WhiteboxPluginPannellum"
            ),
            None,
        )
        return super().setUp()

    def test_plugin_loaded(self):
        self.assertIsNotNone(self.plugin)

    def test_plugin_name(self):
        self.assertEqual(self.plugin.name, "Pannellum")

    def test_bootstrap_assets(self):
        bootstrap_assets = self.plugin.get_bootstrap_assets()

        self.assertIn("css", bootstrap_assets)
        self.assertIn(
            "/static/whitebox_plugin_pannellum/pannellum/pannellum.css",
            bootstrap_assets["css"],
        )

        self.assertIn("js", bootstrap_assets)
        self.assertIn(
            "/static/whitebox_plugin_pannellum/pannellum/pannellum.js",
            bootstrap_assets["js"],
        )
        self.assertIn(
            "/static/whitebox_plugin_pannellum/pannellum/videojs-pannellum-plugin.js",
            bootstrap_assets["js"],
        )
