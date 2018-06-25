C:\Users\g2elab\Anaconda2\python.exe -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. admin.proto

copy admin_pb2.py ..\..\projects\admm_cigre\source
copy admin_pb2_grpc.py ..\..\projects\admm_cigre\source