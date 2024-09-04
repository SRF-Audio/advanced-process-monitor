import psutil
import time
from collections import defaultdict
import curses
import threading

class ProcessMonitor:
    def __init__(self, window_size=300):  # 5 minutes at 1 second intervals
        self.window_size = window_size
        self.process_data = defaultdict(lambda: defaultdict(lambda: [0] * window_size))
        self.lock = threading.Lock()

    def update(self):
        with self.lock:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'num_threads', 'nice', 'status']):
                try:
                    pid = proc.info['pid']
                    self.process_data[pid]['name'] = proc.info['name']
                    self.process_data[pid]['username'] = proc.info['username']
                    self.process_data[pid]['cpu'].append(proc.info['cpu_percent'])
                    self.process_data[pid]['cpu'] = self.process_data[pid]['cpu'][-self.window_size:]
                    self.process_data[pid]['memory'].append(proc.info['memory_percent'])
                    self.process_data[pid]['memory'] = self.process_data[pid]['memory'][-self.window_size:]

                    # Handling I/O counters separately
                    try:
                        io_counters = proc.io_counters()
                        self.process_data[pid]['io_read'].append(io_counters.read_bytes)
                        self.process_data[pid]['io_write'].append(io_counters.write_bytes)
                    except (psutil.AccessDenied, AttributeError):
                        self.process_data[pid]['io_read'].append(0)
                        self.process_data[pid]['io_write'].append(0)

                    self.process_data[pid]['threads'].append(proc.info['num_threads'])
                    self.process_data[pid]['nice'] = proc.info['nice']
                    self.process_data[pid]['status'] = proc.info['status']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

    def get_process_impact(self):
        impacts = []
        with self.lock:
            for pid, data in self.process_data.items():
                if len(data['cpu']) < 2:  # Skip processes with insufficient data
                    continue

                # Filter out None values
                valid_cpu_data = [cpu for cpu in data['cpu'] if cpu is not None]
                valid_memory_data = [mem for mem in data['memory'] if mem is not None]
                valid_thread_data = [threads for threads in data['threads'] if threads is not None]

                # Skip if no valid data points are found
                if not valid_cpu_data or not valid_memory_data or not valid_thread_data:
                    continue

                # Calculate averages safely
                avg_cpu = sum(valid_cpu_data) / len(valid_cpu_data) if valid_cpu_data else 0
                avg_memory = sum(valid_memory_data) / len(valid_memory_data) if valid_memory_data else 0
                avg_threads = sum(valid_thread_data) / len(valid_thread_data) if valid_thread_data else 0

                # Handle I/O rates safely
                io_read_rate = (data['io_read'][-1] - data['io_read'][0]) / len(data['io_read']) if len(data['io_read']) > 1 else 0
                io_write_rate = (data['io_write'][-1] - data['io_write'][0]) / len(data['io_write']) if len(data['io_write']) > 1 else 0

                # Calculate a weighted impact score
                impact_score = (
                    avg_cpu * 0.4 +
                    avg_memory * 0.3 +
                    (io_read_rate + io_write_rate) * 0.0000001 * 0.2 +
                    avg_threads * 0.1
                )

                impacts.append({
                    'pid': pid,
                    'name': data['name'],
                    'username': data['username'],
                    'impact_score': impact_score,
                    'avg_cpu': avg_cpu,
                    'avg_memory': avg_memory,
                    'io_rate': io_read_rate + io_write_rate,
                    'avg_threads': avg_threads,
                    'nice': data['nice'],
                    'status': data['status']
                })

        return sorted(impacts, key=lambda x: x['impact_score'], reverse=True)



def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(1000)

    monitor = ProcessMonitor()

    while True:
        # Get the current size of the terminal window
        height, width = stdscr.getmaxyx()

        monitor.update()
        impacts = monitor.get_process_impact()

        stdscr.clear()
        stdscr.addstr(0, 0, "PID    Name                 User     Impact   CPU%   Mem%    I/O (B/s)  Threads  Nice  Status")

        # Determine the number of processes to display based on terminal height
        max_processes_to_display = min(20, height - 5)  # Adjust based on the available height
        for i, proc in enumerate(impacts[:max_processes_to_display], 1):
            try:
                # Ensure we don't exceed the width of the terminal window
                stdscr.addstr(
                    i, 0,
                    f"{proc['pid']:<6} {proc['name'][:20]:<20} {proc['username'][:8]:<8} {proc['impact_score']:>7.2f} "
                    f"{proc['avg_cpu']:>6.2f} {proc['avg_memory']:>6.2f} {proc['io_rate']:>11.0f} {proc['avg_threads']:>8.2f} "
                    f"{proc['nice']:>5} {proc['status']}"
                )
            except curses.error:
                pass  # Ignore the error and continue

        # Check if there is enough space to display the footer message
        if height > max_processes_to_display + 2:
            try:
                stdscr.addstr(height - 2, 0, "Press 'q' to quit, 'k' to kill a process")
            except curses.error:
                pass

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('k'):
            stdscr.addstr(height - 1, 0, "Enter PID to kill: ")
            curses.echo()
            pid_to_kill = stdscr.getstr().decode('utf-8')
            curses.noecho()
            try:
                psutil.Process(int(pid_to_kill)).terminate()
                stdscr.addstr(height - 1, 0, f"Process {pid_to_kill} terminated.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                stdscr.addstr(height - 1, 0, "Failed to terminate process.")
            stdscr.refresh()
            time.sleep(2)

if __name__ == "__main__":
    curses.wrapper(main)