from pssh.pssh_client import ParallelSSHClient


PI_addrs = ['192.168.1.101', '192.168.1.102', '192.168.1.103', '192.168.1.104', '192.168.1.105',
                    '192.168.1.106', '192.168.1.107', '192.168.1.108', '192.168.1.109', '192.168.1.110']

bus = range(1, 12) + [13, 14]
bus2RPI = range(0, 10) + [0, 1, 2]

#host of bus 1st to bus 10th
host_config1 = {}
for i in bus2RPI[0: 9]:
    host_config1[PI_addrs[i]] = {'user': 'pi', 'password': 'raspberry',
                          'port': 22}
#host of bus 11st to bus 13th
host_config2 = {}
for i in bus2RPI[10: 13]:
    host_config1[PI_addrs[i]] = {'user': 'pi', 'password': 'raspberry',
                          'port': 22}


PATH_TO_PROJECT = 'devel/ACDis/ACAgentgRPC/'
SCENENARIO = 'config_files/default/'

hosts1 = host_config1.keys()
hosts2 = host_config2.keys()

client1 = ParallelSSHClient(hosts1, host_config=host_config1)
client2 = ParallelSSHClient(hosts2, host_config=host_config2)

cmd = 'python ' + PATH_TO_PROJECT + 'source/admm_agent.py -f ' + PATH_TO_PROJECT + SCENENARIO + 'config_agent{0}.json'

host_args1=[{'cmd': cmd.format(i)} for i in bus[0:9]]
host_args2=[{'cmd': cmd.format(i)} for i in bus[10:13]]

output1 = client1.run_command('%(cmd)s', host_args=host_args1)
output2 = client2.run_command('%(cmd)s', host_args=host_args2)

# output = client1.run_command('whoam ')
for host, host_output in output1.items():
    for line in host_output.stdout:
        print("Host [%s] - %s" % (host, line))
for host, host_output in output2.items():
    for line in host_output.stdout:
        print("Host [%s] - %s" % (host, line))
