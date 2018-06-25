C:\Users\g2elab\Anaconda2\python.exe -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. admm.proto

copy admm_pb2.py ..\..\..\admin_consoles\scada_gRPC
copy admm_pb2_grpc.py ..\..\..\admin_consoles\scada_gRPC