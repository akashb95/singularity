"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""

from grpc_tools import protoc

# wd = project root dir
protoc.main((
    '',
    '-I../protos',
    '--python_out=.',
    '--grpc_python_out=.',
    '../protos/element.proto',
    '../protos/location.proto'
    # '../protos/lighting/assets.proto',
    # '../protos/lighting/elements.proto',
    # '../protos/lighting/telecells.proto',
))
