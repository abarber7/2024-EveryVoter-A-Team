import warnings

# Suppress specific Pydantic UserWarnings
warnings.filterwarnings(
    "ignore",
    message="Valid config keys have changed in V2:",
    category=UserWarning
)

warnings.filterwarnings(
    "ignore",
    message='Field "model_id" has conflict with protected namespace "model_".',
    category=UserWarning
)

import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    tests = loader.discover('tests')
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)