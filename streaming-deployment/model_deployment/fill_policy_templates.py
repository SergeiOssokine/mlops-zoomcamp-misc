import logging
import os
from typing import Any, Dict, List, Union

import typer
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.logging import RichHandler
from rich.traceback import install
from typing_extensions import Annotated

# Sets up the logger to work with rich
logger = logging.getLogger(__name__)
logger.addHandler(RichHandler(rich_tracebacks=True, markup=True))
logger.setLevel("INFO")
# Setup rich to get nice tracebacks
install()


def get_params(
    env_file: Union[str, None] = None,
    required_keys: List[str] = [
        "ACCOUNT",
        "REGION",
        "BUCKET_NAME",
        "INPUT_STREAM",
        "OUTPUT_STREAM",
    ],
):

    params = {}
    if env_file is None:
        for key in required_keys:
            k = key.lower()
            params[k] = os.getenv(key)
    else:
        logger.info(f"Reading {env_file}")
        with open(env_file) as stream:
            try:
                params = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc.message)
                raise exc
    return params


def render_template(
    template_file: str, params: Dict[str, Any], output_dir: str = "iam_docs"
):
    env = Environment(
        loader=FileSystemLoader("./iam_templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(template_file)

    result_name = template_file[:-6] + ".json"
    rendered = template.render(**params)
    with open(os.path.join(output_dir, result_name), "w") as fw:
        fw.write(rendered)


def main(
    env_file: Annotated[
        str, typer.Option(help="Yaml file defining env variables")
    ] = None
):
    """Generate policy json files from templates
    Requires: [ACCOUNT,REGION,BUCKET_NAME,INPUT_STREAM,OUTPUT_STREAM]
    Raises:
        ValueError: If all needed env variables are not set
    """

    logger.info("Creating policy documents")
    logger.info("Getting env vars")
    params = get_params(env_file=env_file)

    missing = []
    for k, v in params.items():
        if v is None:
            missing.append(k)
    if missing:
        missing = [x.upper() for x in missing]
        logger.critical(f"The following env variables were not defined: {missing}")
        raise ValueError(f"Some requried env variables were not defined!")

    # Allow Lambda to read from S3 bucket with the model
    logger.info("Creating policy to allow Lambda to read from S3")
    render_template("read_permission_model.jinja", params)
    # Allow Lambda to write to the output stream
    logger.info("Creating policy to write to output kinesis stream")
    render_template("kinesis_write_policy.jinja", params)
    logger.info("All done, output written to ./iam_docs")


if __name__ == "__main__":
    typer.run(main)
