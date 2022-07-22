import os
import shlex
import socket
import subprocess
import sys
from threading import Thread, Lock
from queue import Queue

__all__ = [
    'DATA_DIR',
    'DATASETS',
    'shell',
    'run_parallel_with_gpus',
]


# install python path
parent_dir = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], '../'))
os.environ['PYTHONPATH'] = parent_dir + ':' + os.environ.get('PYTHONPATH', '')
os.environ['PYTHONUNBUFFERED'] = '1'
# sys.path.insert(0, parent_dir)


# detect the data-dir
HOSTNAME = socket.gethostname()
if HOSTNAME.endswith('.cluster.peidan.me'):
    DATA_DIR = '/srv/data/tracegnn'
else:
    DATA_DIR = './data'


# the datasets
DATASETS = [
    'service1',
    'service2', 'service2l',
    'multisvc1',
    'multisvc2', 'multisvc2l'
]


# util to run command
def shell(args, get_output=False):
    if isinstance(args, str):
        args = shlex.split(args)
    args = [s for s in args if s]
    print(f'> {args}', file=sys.stderr)

    if get_output:
        return subprocess.check_output(args).decode('utf-8')
    return subprocess.check_call(args)


# util to run a list of processes with assigned GPUs
def run_parallel_with_gpus(arg_list, gpu_list):
    # initialize the gpus
    gpu_queue = Queue()
    for gpu in gpu_list:
        gpu_queue.put(gpu)

    # initialize the jobs
    mutex = Lock()
    running = True
    proc_list = []

    def run_job(arg):
        gpu = gpu_queue.get()
        gpu = str(gpu)
        proc = None
        try:
            with mutex:
                if running:
                    arg = arg(gpu)
                    env = os.environ.copy()
                    env['TZ'] = 'Asia/Shanghai'
                    env['CUDA_VISIBLE_DEVICES'] = gpu
                    env['PYTHONUNBUFFERED'] = '1'
                    proc = subprocess.Popen(
                        arg,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
                    print(f'[{proc.pid}] {arg}', file=sys.stderr)
                    proc_list.append(proc)

            if proc is not None:
                try:
                    while True:
                        line = proc.stdout.readline()
                        if not line:
                            break
                        print(f'[{proc.pid}] {line.decode("utf-8").rstrip()}', file=sys.stderr)
                    proc.wait()
                finally:
                    print(f'[{proc.pid}] exit code = {proc.returncode}', file=sys.stderr)
        finally:
            gpu_queue.put(gpu)

    threads = []
    try:
        for arg in arg_list:
            thread = Thread(target=run_job, args=(arg,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
    finally:
        with mutex:
            running = False
        for proc in proc_list:
            proc.terminate()
        for thread in threads:
            thread.join()
