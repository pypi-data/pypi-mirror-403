from pathlib import Path

from container_tools.devcontainer import Devcontainer


def test_parse_docker_image():
    devcontainer_path = Path(__file__).parent / "devcontainer.json"

    dev = Devcontainer(devcontainer_path)
    dev.parse()

    assert dev.image == "mcr.microsoft.com/devcontainers/base:ubuntu-22.04"
    assert dev.mounts == [
        "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached",
        "source=devcontainer-cache,target=/cache,type=volume",
        "source=/etc/timezone,target=/etc/timezone,type=bind,readonly",
    ]
    assert dev.containerEnv == {"APP_ENV": "development", "DEBUG": "true", "API_URL": "http://localhost:3000", "EMPTY_VAR": ""}
