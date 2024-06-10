import base64
import json
import os
from typing import Dict, Union

import boto3
import mlflow

kinesis_client = boto3.client("kinesis")
PREDICTIONS_STREAM_NAME = os.getenv("PREDICTIONS_STREAM_NAME", "ride_predictions")

# This should be an artifact that was stored by MLflow
logged_model = os.getenv("LOGGED_MODEL")
model = mlflow.pyfunc.load_model(logged_model)

# For running locally, without sending a stream
TEST_RUN = os.getenv("TEST_RUN", "False") == "True"


def prepare_features(
    ride: Dict[str, Union[str, float]]
) -> Dict[str, Union[str, float]]:
    """Create the features to be used by the model.
    Here we combine the pickup and drop-off locations into 1 feature
    since that _pair_ is likely to determine the duration of the ride.
    We also include the trip distance since it again is likely to
    determine the duration of the ride.

    Args:
        ride (Dict[str, Union[str, float]]): The input dict

    Returns:
        Dict[str, Union[str, float]]: The data ready for predictions
    """
    features = {}
    features["PU_DO"] = "%s_%s" % (ride["PULocationID"], ride["DOLocationID"])
    features["trip_distance"] = ride["trip_distance"]
    return features


def predict(features: Dict[str, Union[str, float]]) -> float:
    """Predict the duration of the ride

    Args:
        features (Dict[str, Union[str, float]]): Input data

    Returns:
        float: The duration of the ride, in minutes
    """
    pred = model.predict(features)
    return float(pred[0])


def lambda_handler(event, context):

    predictions_events = []

    # Iterate over every input
    for record in event["Records"]:

        # Retrieve and decode the data
        encoded_data = record["kinesis"]["data"]
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        ride_event = json.loads(decoded_data)
        ride = ride_event["ride"]
        ride_id = ride_event["ride_id"]

        # Predict the duration
        features = prepare_features(ride)
        prediction = predict(features)

        prediction_event = {
            "model": "ride_duration_prediction_model",
            "version": "123",
            "prediction": {"ride_duration": prediction, "ride_id": ride_id},
        }

        # Send the data to the output stream if we have a production run
        if not TEST_RUN:
            kinesis_client.put_record(
                StreamName=PREDICTIONS_STREAM_NAME,
                Data=json.dumps(prediction_event),
                PartitionKey=str(ride_id),
            )

        predictions_events.append(prediction_event)

    return {"predictions": predictions_events}
