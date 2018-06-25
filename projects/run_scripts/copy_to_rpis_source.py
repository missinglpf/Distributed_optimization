import subprocess

subprocess.call('whoami')

PI_addrs = ['192.168.1.101', '192.168.1.102', '192.168.1.103', '192.168.1.104', '192.168.1.105',
                    '192.168.1.106', '192.168.1.107', '192.168.1.108', '192.168.1.109', '192.168.1.110']

bus2PI = range(0, 10) + [0, 1, 2]

for i in PI_addrs:
    cmd = r'pscp -r -pw raspberry E:\lam\Distributed_optimization\projects\admm_cigre\source\ ' + \
        'pi@{0}:/home/pi/devel/ACDis/ACAgentgRPC/source'
    subprocess.call(cmd.format(i))

