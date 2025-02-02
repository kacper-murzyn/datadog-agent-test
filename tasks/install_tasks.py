import os
import sys

from invoke import Exit, task

from .libs.common.utils import color_message, environ

TOOL_LIST = [
    'github.com/frapposelli/wwhrd',
    'github.com/go-enry/go-license-detector/v4/cmd/license-detector',
    'github.com/golangci/golangci-lint/cmd/golangci-lint',
    'github.com/goware/modvendor',
    'github.com/stormcat24/protodep',
    'gotest.tools/gotestsum',
    'github.com/vektra/mockery/v2',
]

TOOL_LIST_PROTO = [
    'github.com/favadi/protoc-go-inject-tag',
    'github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway',
    'github.com/golang/protobuf/protoc-gen-go',
    'github.com/golang/mock/mockgen',
    'github.com/planetscale/vtprotobuf/cmd/protoc-gen-go-vtproto',
    'github.com/tinylib/msgp',
]

TOOLS = {
    'internal/tools': TOOL_LIST,
    'internal/tools/proto': TOOL_LIST_PROTO,
}


@task
def download_tools(ctx):
    """Download all Go tools for testing."""
    with environ({'GO111MODULE': 'on'}):
        for path, _ in TOOLS.items():
            with ctx.cd(path):
                ctx.run("go mod download")


@task
def install_tools(ctx):
    """Install all Go tools for testing."""
    if os.path.isfile("go.work") or os.path.isfile("go.work.sum"):
        # Someone reported issues with this command when using a go.work but other people
        # use a go.work and don't have any issue, so the root cause is unclear.
        # Printing a warning because it might help someone but not enforcing anything.

        # The issue which was reported was that `go install` would fail with the following error:
        ### no required module provides package <package>; to add it:
        ### go get <package>
        print(
            color_message(
                "WARNING: In case of issue, you might want to try disabling go workspaces by setting the environment variable GOWORK=off, or even deleting go.work and go.work.sum",
                "orange",
            )
        )

    with environ({'GO111MODULE': 'on'}):
        for path, tools in TOOLS.items():
            with ctx.cd(path):
                for tool in tools:
                    ctx.run(f"go install {tool}")


@task
def install_shellcheck(ctx, version="0.8.0", destination="/usr/local/bin"):
    """
    Installs the requested version of shellcheck in the specified folder (by default /usr/local/bin).
    Required to run the shellcheck pre-commit hook.
    """

    if sys.platform == 'win32':
        print("shellcheck is not supported on Windows")
        raise Exit(code=1)
    if sys.platform.startswith('darwin'):
        platform = "darwin"
    if sys.platform.startswith('linux'):
        platform = "linux"

    ctx.run(
        f"wget -qO- \"https://github.com/koalaman/shellcheck/releases/download/v{version}/shellcheck-v{version}.{platform}.x86_64.tar.xz\" | tar -xJv -C /tmp"
    )
    ctx.run(f"cp \"/tmp/shellcheck-v{version}/shellcheck\" {destination}")
    ctx.run(f"rm -rf \"/tmp/shellcheck-v{version}\"")
