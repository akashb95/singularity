"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""
import logging
import os
import re

from grpc_tools import protoc

import settings as lighting_settings
from log import setup_logger

generated_files_outdir = "./lib"

logger = setup_logger("codegen", logging.DEBUG)

if __name__ == "__main__":
    lighting_settings.load_env_vars(False)
    abs_path_codegen_outdir = os.path.join(os.getcwd(), generated_files_outdir)

    if not os.path.exists(abs_path_codegen_outdir):
        os.makedirs(abs_path_codegen_outdir)

    protoc.main((
        '',
        '-I../protos',
        '-I{}'.format(os.getenv("DEFAULT_PROTOS_INCLUDE_PATH")),
        '--python_out={}'.format(generated_files_outdir),
        '--grpc_python_out={}'.format(generated_files_outdir),
        '../protos/asset.proto',
        '../protos/basestation.proto',
        '../protos/element.proto',
        '../protos/location.proto',
        '../protos/telecell.proto',
        '../protos/user.proto'
    ))

    for file in os.listdir(abs_path_codegen_outdir):
        # look for only .py files - skip all others
        if not file.endswith(".py"):
            continue

        logger.info("Modifying imports in file: {}".format(file))

        # read in code to memory
        with open(os.path.join(abs_path_codegen_outdir, file), "r") as generated_file:
            code = generated_file.read()

        # modify code in memory using regex
        # e.g: import location_pb2 as location__pb2  --->  from . import location_pb2 as location__pb2
        code_modified_imports = re.sub("(^import .*_pb2 as .*__pb2)", r"from . \1", code, flags=re.M)

        # write to code file
        with open(os.path.join(abs_path_codegen_outdir, file), "w") as generated_file:
            generated_file.write(code_modified_imports)
