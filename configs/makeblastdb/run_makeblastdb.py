#!/usr/bin/env python
import time
import subprocess


def main():
    print('{{ id }}')
    command=['ls','-l']
    elapsed_time = None
    with open('{{ out_log }}', 'w') as out_log, open('{{ err_log }}', 'w') as err_log:
        start = time.time()
        proc = subprocess.Popen(command, stdout=out_log, stderr=err_log)
        proc.wait()
        out_log.flush()
        err_log.flush()
        elapsed_time = time.time() - start
    with open('{{ computing_time_log }}', 'w') as output:
        output.write(str(elapsed_time))


if __name__ == '__main__':
    main()
