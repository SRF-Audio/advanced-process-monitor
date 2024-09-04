import os
import subprocess
from datetime import datetime

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

# List of optimizations to toggle
OPTIMIZATIONS = [
    "sudo mdutil -a -i off",
    "sudo tmutil disable",
]

def log_action(action, success=True):
    status = "Success" if success else "Failed"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{datetime.now()}: {status}: {action}\n")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_action(command)
        return True, result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        log_action(f"{command} - {e.stderr.decode('utf-8')}", success=False)
        return False, e.stderr.decode('utf-8')

def check_full_disk_access():
    command = "spctl --assess --type execute /System/Applications/Utilities/Terminal.app"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stderr.decode('utf-8').strip()
    
    return output == ""


def disable_services():
    for service in SERVICES:
        run_command(f"launchctl unload -w {service}")

def enable_services():
    for service in SERVICES:
        run_command(f"launchctl load -w {service}")

def optimize_settings():
    if check_full_disk_access():
        for optimization in OPTIMIZATIONS:
            run_command(optimization)
    else:
        log_action("Full Disk Access not enabled for Terminal. Skipping disk-related optimizations.", success=False)

def restore_settings():
    if check_full_disk_access():
        for optimization in OPTIMIZATIONS:
            restored_command = optimization.replace("off", "on").replace("disable", "enable")
            run_command(restored_command)
    else:
        log_action("Full Disk Access not enabled for Terminal. Skipping disk-related optimizations.", success=False)

if __name__ == "__main__":
    start_time = datetime.now()
    if not os.path.exists(PERFORMANCE_MODE_FLAG):
        print("Enabling performance mode...")
        log_action("Enabling performance mode")
        disable_services()
        optimize_settings()
        open(PERFORMANCE_MODE_FLAG, 'a').close()
        log_action("Performance mode enabled")
    else:
        print("Disabling performance mode...")
        log_action("Disabling performance mode")
        enable_services()
        restore_settings()
        os.remove(PERFORMANCE_MODE_FLAG)
        log_action("Performance mode disabled")

    end_time = datetime.now()
    log_action(f"Total execution time: {end_time - start_time}")
    print("Operation complete.")
