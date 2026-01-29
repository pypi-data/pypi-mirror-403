#! /usr/bin/env python3
"""
docstring
"""

from pathlib import Path
from os import chdir
import argparse
import time

import dawgdad as dd
import pandas as pd
import numpy as np


def main():
    chdir(Path(__file__).parent.resolve())  # required for cron
    df = dd.read_file(file_name="x_mr_example.xlsx")
    print(df)


if __name__ == "__main__":
    main()
