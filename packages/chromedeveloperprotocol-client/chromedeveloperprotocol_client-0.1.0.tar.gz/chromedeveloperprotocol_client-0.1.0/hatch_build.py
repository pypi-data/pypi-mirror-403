import sys
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class BuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from cdp.generator import CDPGenerator
        print("Generating CDP client code...")
        generator = CDPGenerator()
        generator.generate()
