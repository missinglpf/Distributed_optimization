#!/usr/bin/env bash

# generate the python RPC server and stubs from the proto file
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. admin.proto
# copy the files also in the scada project
cp -f admin_pb2.py ../../projects/DGridAgentgRPC/sources/
cp -f admin_pb2_grpc.py ../../projects/DGridAgentgRPC/sources/