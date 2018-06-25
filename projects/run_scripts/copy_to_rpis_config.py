import subprocess
from pssh.pssh_client import ParallelSSHClient

host_config = {'192.168.1.101' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.102' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.103' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.104' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.105' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.106' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.107' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.108' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.109' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22}
               # '192.168.1.110' : {'user': 'pi', 'password': 'raspberry',
               #            'port': 22}
               }

hosts = host_config.keys()
#
PATH_TO_PROJECT = 'devel/ACDis/ACAgentgRPC/'
CONFIG = 'default'
#
client = ParallelSSHClient(hosts, host_config=host_config)
output = client.run_command('mkdir ' + PATH_TO_PROJECT + 'config_files')
# output = client.run_command('mkdir ' + PATH_TO_PROJECT + 'config_files/' + CONFIG)
# for host, host_output in output.items():
#     for line in host_output.stdout:
#         print("Host [%s] - %s" % (host, line))

for i in hosts:
    cmd = r'pscp -r -pw raspberry E:\lam\Distributed_optimization\projects\admm_cigre\config_files\ ' + CONFIG + ' ' + \
          'pi@{0}:/home/pi/devel/ACDis/ACAgentgRPC/config_files/'
    subprocess.call(cmd.format(i))

