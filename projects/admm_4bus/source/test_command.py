import subprocess

# agents = [1, 2, 3, 4, lamda10, 6, 7, 8, 9]
# agents = [0, 1, 2, 3]
agents = [0, 1, 2, 3, 4, 5]
cm_run_agent = "start C:\\ProgramData\\Anaconda2\\python.exe D:\\phd\\These_asys\\Distributed_optimization\\projects\\admm_4bus\\source\\admm_agent.py -f ../config/sixbus/config_A_{0}.json"
for i in agents:
    print cm_run_agent.format(i)
    subprocess.Popen(cm_run_agent.format(i), shell=True)