import psutil

def test_psutil_attributes():
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'num_threads', 'nice', 'status']):
        try:
            print(f"PID: {proc.info['pid']}")
            print(f"Name: {proc.info['name']}")
            print(f"Username: {proc.info['username']}")
            print(f"CPU%: {proc.info['cpu_percent']}")
            print(f"Memory%: {proc.info['memory_percent']}")
            print(f"Number of Threads: {proc.info['num_threads']}")
            print(f"Nice: {proc.info['nice']}")
            print(f"Status: {proc.info['status']}")
            print('-' * 40)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Process access issue: {e}")

if __name__ == "__main__":
    test_psutil_attributes()
