import os

import yaml
from pytest import fixture


@fixture()
def golden(request):
    with open(request.param, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    config["filename"] = os.path.basename(request.param)

    yield config
