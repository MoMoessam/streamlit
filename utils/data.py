import pandas as pd
from utils.config import ORDERS
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "titanic (1).csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.lower()
    df["class"] = df["pclass"].map({1: "First", 2: "Second", 3: "Third"})
    df["survival"] = df["survived"].map({0: "Died", 1: "Survived"})
    df["port"] = df["embarked"].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
    df["family_size"] = df["sibsp"] + df["parch"] + 1
    df["title"] = df["name"].str.extract(r",\s*([^\.]+)\.", expand=False)
    df["age_group"] = pd.cut(
        df["age"], [0, 12, 18, 35, 60, 80],
        labels=ORDERS["age_group"],
    )
    return df