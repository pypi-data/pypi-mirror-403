import logging
from pathlib import Path
from typing import Annotated
import typer
import yaml

from champions.model.datacard import DataCard
from champions.model.settings import EvalSettings, TrainSettings
from champions.service.datacardhelper import dataCardHelper
from champions.service.eval import Eval
from champions.service.train import Train


logger = logging.getLogger(__name__)

app = typer.Typer()


# def main(config: Annotated[typer.FileText, typer.Option()]):
@app.command()
def train(
    datacard: Annotated[typer.FileText, typer.Option()],
    trainsettings: Annotated[typer.FileText, typer.Option()],
):
    train = Train(
        dc=DataCard(**yaml.safe_load(datacard)),
        settings=TrainSettings(**yaml.safe_load(trainsettings)),
    )
    train.run()


@app.command()
def eval(
    datacard: Annotated[typer.FileText, typer.Option()],
    evalsettings: Annotated[typer.FileText, typer.Option()],
):
    train = Eval(
        dc=DataCard(**yaml.safe_load(datacard)),
        settings=EvalSettings(**yaml.safe_load(evalsettings)),
    )
    train.run()


@app.command()
def create_dc(
    src: Annotated[Path, typer.Option()],
    out: Annotated[Path, typer.Option(prompt=True)],
):
    helper = dataCardHelper(src=src, out=out)
    helper.run()


# if __name__ == "__main__":
#     # Profilierung des Typer-Befehls
#     profiler = cProfile.Profile()
#     run_path = Path(
#         "/Users/swayand/PycharmProjects/champions/examples/diabetes_prediction_challenge"
#     )
#     datacard = run_path / "diabetes_prediction_challenge.yaml"
#     trainsettings = run_path / "train_settings.yaml"
#     profiler.enable()

#     train(datacard=datacard.open(), trainsettings=trainsettings.open())
#     profiler.disable()
#     # sprofiler.print_stats(sort="time")

#     stats = pstats.Stats(profiler)
#     # Sort by different metrics
#     stats.sort_stats("cumulative").print_stats(
#         10
#     )  # Top 10 functions by cumulative time
#     # stats.sort_stats('calls').print_stats(10)       # Top 10 functions by call count
#     stats.sort_stats("time").print_stats(10)  # Top 10 functions by time
