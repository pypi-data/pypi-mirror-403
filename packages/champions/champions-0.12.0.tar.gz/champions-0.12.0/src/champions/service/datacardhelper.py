from pathlib import Path
from pydantic import BaseModel
import polars as pl
import typer
import yaml


class dataCardHelper(BaseModel):
    src: Path
    out: Path

    def run(self):
        df = self.get_df()

        while True:
            print(f"One of {df.columns}")
            target_feature = typer.prompt("Chose target column")
            if target_feature in df.columns:
                break
        target = {
            "feature_name": target_feature,
            "values": df[target_feature].unique().to_list(),
        }

        features = []
        for col in df.columns:
            akt_type = self.get_type(str(df[col].dtype))
            stat_type = "numerical" if akt_type in ["int", "float"] else "categorial"
            stat_type = "categorial" if target_feature == col else stat_type
            feature = {"name": col, "statistical": stat_type, "type": akt_type}
            if df[col].has_nulls():
                null_value = typer.prompt(
                    f"{col} has null values. What should be the null value (type {akt_type})?"
                )
                feature["missing_value"] = null_value

            features.append(feature)

        infos = typer.prompt("Infos about the dataset")
        dc = {
            "features": features,
            "target": target,
            "infos": {"bla": infos},
            "train_files": [str(self.src)],
            "test_files": [str(self.src)],
        }

        with self.out.open("w") as out_file:
            yaml.dump(dc, out_file)

    def get_type(self, dtype: str) -> str:
        match dtype:
            case "Int64":
                return "int"
            case "Float64":
                return "float"
            case "String":
                return "string"

        raise ValueError(f"Unsupported data type: {dtype}")

    def get_df(self) -> pl.DataFrame:
        if self.src.name.endswith(".csv"):
            return pl.read_csv(self.src)
        elif self.src.name.endswith(".parquet"):
            return pl.read_parquet(self.src)
        else:
            raise ValueError("Unsupported file type")
