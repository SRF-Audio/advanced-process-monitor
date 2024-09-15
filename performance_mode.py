import os
import subprocess
from datetime import datetime

# Constants for applications and optional project paths
APPLICATIONS = [
    {"app_path": "/Applications/Focusrite Control 2.app", "project_path": None},
    {"app_path": "/Applications/Logic Pro X.app", "project_path": "~/Music/Logic/Live Set.logicx"}
]

PERFORMANCE_MODE_FLAG = "/tmp/performance_mode_active"
LOG_FILE = "/tmp/performance_mode.log"

# List of services to manage
SERVICES = [
    "/System/Library/LaunchAgents/com.apple.notificationcenterui.plist",
    "/System/Library/LaunchAgents/com.apple.spotlight.plist",
    "/System/Library/LaunchDaemons/com.apple.wifip2pd.plist",
    "/System/Library/LaunchDaemons/com.apple.wifiFirmwareLoader.plist",
    "/System/Library/LaunchDaemons/com.apple.wifianalyticsd.plist",
    "/System/Library/LaunchDaemons/com.apple.wifivelocityd.plist",
    "/System/Library/LaunchDaemons/com.apple.bluetoothd.plist",
    "/System/Library/LaunchAgents/com.apple.BluetoothUIService.plist",
    "/System/Library/LaunchDaemons/com.apple.diagnosticextensions.osx.spotlight.helper.plist",
    "/System/Library/LaunchDaemons/com.apple.icloud.searchpartyd.plist",
    "/System/Library/LaunchDaemons/com.apple.icloud.findmydeviced.plist",
    "/Library/LaunchAgents/com.logitech.logitune.updater.plist",
    "/Library/LaunchAgents/com.logitech.logitune.launcher.plist",
    "/Library/LaunchDaemons/com.adobe.acc.installer.v2.plist",
    "/Library/LaunchAgents/com.adobe.ccxprocess.plist",
    "/Library/LaunchAgents/com.adobe.AdobeCreativeCloud.plist",
    "/Library/LaunchAgents/com.adobe.coresync.plist",
    "/Library/LaunchAgents/com.audinate.dante.DanteVia.DanteViaLoader.plist",
    "/Library/LaunchDaemons/com.audinate.dante.ConMon.plist",
    "/Library/LaunchDaemons/com.audinate.dante.DanteVia.DanteViaDaemon.plist"
]

# List of process names to search and kill
PROCESSES = [
    "Adobe",
    "OneDrive",
    "DanteViaAudioHelper"
]

# List of optimizations to toggle
OPTIMIZATIONS = [
    "sudo mdutil -a -i off",
    "sudo tmutil disable",
    "sudo pmset -a gpuswitch 0",  # Disable automatic graphics switching
    "sudo pmset -a sleep 0",  # Disable system sleep
    "defaults write NSGlobalDomain NSAppSleepDisabled -bool YES",  # Disable App Nap
    "sudo tmutil disablelocal",  # Turn off Time Machine local backups
    "sudo defaults write /Library/Preferences/com.apple.Bluetooth.plist ControllerPowerState 0",  # Disable Bluetooth discovery
]

# List of restoration commands to toggle back after session
RESTORATION_COMMANDS = [
    "sudo pmset -a gpuswitch 1",  # Re-enable automatic graphics switching
    "sudo pmset -a sleep 1",  # Re-enable system sleep
    "defaults write NSGlobalDomain NSAppSleepDisabled -bool NO",  # Re-enable App Nap
    "sudo tmutil enablelocal",  # Turn on Time Machine local backups
    "sudo defaults write /Library/Preferences/com.apple.Bluetooth.plist ControllerPowerState 1",  # Re-enable Bluetooth discovery
]

def log_action(action, success=True):
    """
    Logs actions to a log file with a timestamp.
    
    :param action: The action being logged.
    :param success: Boolean indicating if the action succeeded.
    """
    status = "Success" if success else "Failed"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{datetime.now()}: {status}: {action}\n")

def run_command(command):
    """
    Executes a shell command and logs the result.
    
    :param command: Shell command to be executed.
    :return: Tuple (success, output/error message).
    """
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_action(command)
        return True, result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        log_action(f"{command} - {e.stderr.decode('utf-8')}", success=False)
        return False, e.stderr.decode('utf-8')

def check_full_disk_access():
    """
    Checks if the script has full disk access in macOS.
    
    :return: True if full disk access is granted, False otherwise.
    """
    command = "spctl --assess --type execute /System/Applications/Utilities/Terminal.app"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stderr.decode('utf-8').strip()
    
    return output == ""

def disable_services():
    """
    Disables a predefined list of background services using `launchctl`.
    """
    for service in SERVICES:
        run_command(f"launchctl unload -w {service}")

def enable_services():
    """
    Re-enables the services that were disabled earlier using `launchctl`.
    """
    for service in SERVICES:
        run_command(f"launchctl load -w {service}")

def kill_processes(process_names):
    """
    Kills specific processes by name.
    
    :param process_names: List of process names to search for and terminate.
    """
    try:
        result = subprocess.run("ps aux", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes = result.stdout.decode('utf-8').splitlines()

        for process_name in process_names:
            for process in processes:
                if process_name in process:
                    try:
                        pid = int(process.split()[1])  
                        run_command(f"kill -9 {pid}")
                        log_action(f"Killed {process_name} process with PID: {pid}")
                    except (IndexError, ValueError):
                        log_action(f"Failed to parse PID for {process_name}: {process}", success=False)
    except subprocess.CalledProcessError as e:
        log_action(f"Failed to list processes: {e.stderr.decode('utf-8')}", success=False)

def toggle_wifi(enable):
    """
    Toggles WiFi on or off.
    
    :param enable: True to enable WiFi, False to disable.
    """
    command = "networksetup -setairportpower en0 on" if enable else "networksetup -setairportpower en0 off"
    run_command(command)
    log_action("WiFi enabled" if enable else "WiFi disabled")

def toggle_bluetooth(enable):
    """
    Toggles Bluetooth on or off.
    
    :param enable: True to enable Bluetooth, False to disable.
    """
    command = "blueutil --power 1" if enable else "blueutil --power 0"
    run_command(command)
    log_action("Bluetooth enabled" if enable else "Bluetooth disabled")

def optimize_settings():
    """
    Applies system optimizations for audio performance, such as disabling sleep, graphics switching, etc.
    """
    if check_full_disk_access():
        for optimization in OPTIMIZATIONS:
            run_command(optimization)
    else:
        log_action("Full Disk Access not enabled for Terminal. Skipping disk-related optimizations.", success=False)

def restore_settings():
    """
    Restores system settings that were modified for performance optimizations.
    """
    if check_full_disk_access():
        for command in RESTORATION_COMMANDS:
            run_command(command)
    else:
        log_action("Full Disk Access not enabled for Terminal. Skipping disk-related optimizations.", success=False)

def expand_path(path):
    """
    Expands the tilde (~) to the full home directory path.
    
    :param path: The file or project path to expand.
    :return: Expanded full path.
    """
    return os.path.expanduser(path)

def open_applications(applications):
    """
    Opens predefined applications with optional project paths, expanding paths as needed.
    
    :param applications: List of dictionaries with app paths and optional project paths.
    """
    for app in applications:
        app_path = app["app_path"]
        project_path = expand_path(app["project_path"]) if app["project_path"] else None
        
        if project_path:
            subprocess.run(["open", "-a", app_path, project_path])
        else:
            subprocess.run(["open", "-a", app_path])

if __name__ == "__main__":
    start_time = datetime.now()
    
    if not os.path.exists(PERFORMANCE_MODE_FLAG):
        print("Enabling performance mode...")
        log_action("Enabling performance mode")
        disable_services()
        kill_processes(PROCESSES)  
        toggle_wifi(False)
        toggle_bluetooth(False)
        optimize_settings()
        open(PERFORMANCE_MODE_FLAG, 'a').close()
        log_action("Performance mode enabled")
        print("Performance mode enabled.")

        # Open applications
        open_applications(APPLICATIONS)

    else:
        print("Disabling performance mode...")
        log_action("Disabling performance mode")
        enable_services()
        toggle_wifi(True)
        toggle_bluetooth(True)
        restore_settings()
        os.remove(PERFORMANCE_MODE_FLAG)
        log_action("Performance mode disabled")
        print("Performance mode disabled.")

    end_time = datetime.now()
    log_action(f"Total execution time: {end_time - start_time}")
    print("Operation complete.")
