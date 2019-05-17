import pandas as pd

from typing import Dict, NewType, Set

Email = NewType('Email', str)
FilePath = NewType('FilePath', str)
Matrix = NewType('Matrix', pd.DataFrame)
Name = NewType('Name', str)
Table = NewType('Table', pd.DataFrame)
