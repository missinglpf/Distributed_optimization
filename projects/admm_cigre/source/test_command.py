import subprocess

agents = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]

cm_run_agent = "start C:\\ProgramData\\Anaconda2\\python.exe D:\\phd\\These_asys\\Distributed_optimization\\projects\\admm_cigre\\source\\admm_agent_STRATH.py -f ../config_files/default/config_A_{0}.json"
for i in agents:
    print cm_run_agent.format(i)
    subprocess.Popen(cm_run_agent.format(i), shell=True)