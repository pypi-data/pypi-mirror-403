from django.test import TestCase
from unittest.mock import patch, MagicMock

from plugin.manager import plugin_manager


class TestWhiteboxPluginVideoJS(TestCase):
    def setUp(self) -> None:
        self.plugin = next(
            (
                x
                for x in plugin_manager.whitebox_plugins
                if x.__class__.__name__ == "WhiteboxPluginVideoJS"
            ),
            None,
        )
        return super().setUp()

    def test_plugin_loaded(self):
        self.assertIsNotNone(self.plugin)

    def test_plugin_name(self):
        self.assertEqual(self.plugin.name, "VideoJS")

    def test_bootstrap_assets(self):
        bootstrap_assets = self.plugin.get_bootstrap_assets()

        self.assertIn("css", bootstrap_assets)
        self.assertIn(
            "/static/whitebox_plugin_videojs/videojs/video-js.css",
            bootstrap_assets["css"],
        )

        self.assertIn("js", bootstrap_assets)
        self.assertIn(
            "/static/whitebox_plugin_videojs/videojs/video.min.js",
            bootstrap_assets["js"],
        )
