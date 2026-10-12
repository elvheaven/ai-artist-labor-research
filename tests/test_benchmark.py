import unittest
import os
import json

class TestBenchmarkPipeline(unittest.TestCase):
    def test_config_exists(self):
        self.assertTrue(os.path.exists("config.json"), "config.json should exist in root directory")

    def test_sample_data_exists(self):
        with open("config.json", "r") as f:
            config = json.load(f)
        self.assertTrue(os.path.exists(config["data_path"]), f"Sample dataset not found at {config['data_path']}")

if __name__ == "__main__":
    unittest.main()
