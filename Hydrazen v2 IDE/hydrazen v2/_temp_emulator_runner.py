import importlib.util
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
emulator_path = os.path.join(base_dir, 'hydrazen v2.py')
spec = importlib.util.spec_from_file_location('emulator', emulator_path)
emulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emulator)
emulator.ROM = [177, 2, 241, 0, 128, 3, 177, 1, 241, 0, 16, 0]
emulator.main(60.0, debug=False)
