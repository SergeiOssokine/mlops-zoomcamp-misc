import logging
from typing import Dict, List, Union

import mlflow
import pandas as pd
import pandera as pa
import typer
from rich.logging import RichHandler
from rich.traceback import install
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import make_pipeline
from typing_extensions import Annotated

# Sets up the logger to work with rich
logger = logging.getLogger(__name__)
logger.addHandler(RichHandler(rich_tracebacks=True, markup=True))
logger.setLevel("INFO")
# Setup rich to get nice tracebacks
install()


# Basic pandera validation schema for our data
schema = pa.DataFrameSchema(
    columns={
        "PULocationID": pa.Column(int, coerce=True),
        "DOLocationID": pa.Column(int, coerce=True),
        "trip_distance": pa.Column(float, pa.Check.ge(0.0)),
    }
)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Check that the features we care about are present
    and obey some basic sanity checks

    Args:
        df (pd.DataFrame): Raw data

    Returns:
        pd.DataFrame: Validated data
    """
    try:
        validated_df = schema(df)
    except pa.errors.SchemaError as exc:
        print(exc)
        exit(-1)
    return validated_df


def read_dataframe(filename: str) -> pd.DataFrame:
    """Read in the NYC Taxi input data.
    Ensures that the pick-up and drop-off locations
    are stored as strings.

    Args:
        filename (str): Name of file with data

    Returns:
        pd.DataFrame: The data in DataFrame form
    """
    df = pd.read_parquet(filename)

    validate_dataframe(df)
    df["duration"] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ["PULocationID", "DOLocationID"]
    df[categorical] = df[categorical].astype(str)
    return df


def prepare_dictionaries(df: pd.DataFrame) -> List[Dict[str, Union[str, float]]]:
    """Perform feature engineering and prepare dicts containing the
    desired features

    Args:
        df (pd.DataFrame): Data

    Returns:
        List[Dict[str, Union[str, float]]]: List of dicts with the features,
                                            each item being a dict with records
    """
    df["PU_DO"] = df["PULocationID"] + "_" + df["DOLocationID"]
    categorical = ["PU_DO"]
    numerical = ["trip_distance"]
    dicts = df[categorical + numerical].to_dict(orient="records")
    return dicts


def main(
    tracking_uri: Annotated[
        str, typer.Option(help="The MLFlow tracking URI")
    ] = "http://localhost:5012",
    experiment_name: Annotated[
        str, typer.Option(help="The experiment name to use")
    ] = "nyc-taxi-analysis",
):
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    logger.info("Reading data")
    df_train = read_dataframe("./data/green_tripdata_2023-01.parquet")
    df_val = read_dataframe("./data/green_tripdata_2023-02.parquet")

    target = "duration"
    y_train = df_train[target].values
    y_val = df_val[target].values
    logger.info("Preprocessing data")
    dict_train = prepare_dictionaries(df_train)
    dict_val = prepare_dictionaries(df_val)

    # Run the training
    with mlflow.start_run():

        # GBRT are relatively insensitive to over-fitting so we can use
        # a large number of boosting ierations
        params = dict(
            n_estimators=2000, min_samples_leaf=20, learning_rate=0.2, verbose=2
        )
        mlflow.log_params(params)

        pipeline = make_pipeline(DictVectorizer(), GradientBoostingRegressor(**params))
        logger.info("Training model")
        pipeline.fit(dict_train, y_train)
        y_pred = pipeline.predict(dict_val)

        rmse = root_mean_squared_error(y_pred, y_val)

        mlflow.log_metric("rmse", rmse)
        logger.info("Logging model artifact")
        mlflow.sklearn.log_model(pipeline, artifact_path="model")
        logger.info("All done")


if __name__ == "__main__":
    typer.run(main)
