from __future__ import print_function

from pssh.pssh_client import ParallelSSHClient

host_config = {'192.168.1.101' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               '192.168.1.102' : {'user': 'pi', 'password': 'raspberry',
                          'port': 22},
               }
hosts = host_config.keys()
client = ParallelSSHClient(hosts, host_config=host_config)
output = client.run_command('ls')
for host, host_output in output.items():
    for line in host_output.stdout:
        print("Host [%s] - %s" % (host, line))