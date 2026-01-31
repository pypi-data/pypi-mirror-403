import sys
import subprocess
import platform
import subprocess
from zscams.agent.src.support.logger import get_logger

from .filesystem import write_to_file

logger = get_logger("os_support")


def is_linux():
    if sys.platform.lower().startswith("linux"):
        return True
    return False


def system_user_exists(username: str):
    try:
        subprocess.run(
            ["id", username],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.debug("found the system user %s", username)
        return True
    except subprocess.CalledProcessError:
        return False


def is_freebsd():
    return (
        platform.system().lower() == "freebsd"
        or platform.system().lower() == "zscaleros"
    )


def create_system_user(username: str):
    # Support both Linux and FreeBSD
    if not (platform.system() == "Linux" or is_freebsd()):
        logger.error(
            "Error creating system user: This script is intended to run on Linux or FreeBSD systems."
        )
        return

    if not username:
        logger.error("Error creating system user: Username must be provided.")
        return

    # Assuming system_user_exists is already updated to handle both
    if system_user_exists(username):
        logger.warning("User '%s' already exists.", username)
        return

    try:
        if is_freebsd():
            cmd = ["sudo", "pw", "useradd", "-n", username, "-m", "-s", "/bin/sh"]
        else:
            # Standard Linux useradd
            cmd = ["sudo", "useradd", "-m", "-s", "/bin/bash", username]

        subprocess.run(cmd, check=True)
        logger.info("System user '%s' created successfully.", username)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to create user '%s': %s", username, e)


def install_service(service_name: str, content: str):
    """
    Main entry point to install services.
    Redirects to systemd for Linux and rc.d for FreeBSD.
    """
    if is_linux():
        install_systemd_service(service_name, content)
    elif is_freebsd():
        install_rc_service(service_name, content)
    else:
        logger.error("Unsupported OS for service installation.")


def install_rc_service(service_name: str, content: str):
    """
    Installs a FreeBSD rc.d script.
    Note: 'content' for FreeBSD should be a valid rc.subr shell script.
    """
    service_path = f"/usr/local/etc/rc.d/{service_name}"

    try:
        # 1. Write the rc script
        logger.debug("Installing FreeBSD rc script: %s", service_path)
        # Using sudo tee to ensure write permissions on restricted paths
        echo_cmd = f"printf '%s' '{content}' | sudo tee {service_path}"
        subprocess.run(echo_cmd, shell=True, check=True, stdout=subprocess.DEVNULL)

        # 2. Make it executable (Crucial for FreeBSD)
        subprocess.run(["sudo", "chmod", "+x", service_path], check=True)

        # 3. Enable and Start
        # In FreeBSD, enabling adds 'service_name_enable="YES"' to /etc/rc.conf
        logger.debug("Enabling and starting FreeBSD service %s...", service_name)
        subprocess.run(["sudo", "sysrc", f"{service_name}_enable=YES"], check=True)
        subprocess.run(["sudo", "service", service_name, "start"], check=True)

        logger.info("Service %s installed and started successfully.", service_name)

    except Exception as e:
        logger.error("Failed to install FreeBSD service %s: %s", service_name, e)


def install_systemd_service(service_name: str, content: str):
    service_path = f"/etc/systemd/system/{service_name}"

    try:
        logger.debug("Installing service '%s' content", service_name)
        write_to_file(service_path, content)
        logger.debug(f"Installed {service_name}")
    except PermissionError:
        logger.warning("Permission denied: trying to write with sudo...")
        echo_cmd = f"echo '{content}' | sudo tee {service_path}"
        subprocess.run(echo_cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
        logger.debug("Wrote the service")
    except Exception as e:
        logger.error("Failed to install service %s. %s", service_name, e)
        return

    try:
        logger.debug("Enabling %s...", service_name)
        subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
        logger.debug("Starting %s...", service_name)
        subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
    except subprocess.CalledProcessError:
        logger.error(
            "Failed to enable/restart zscams service, You might need to do that manually by running\nsudo systemctl enable %s && sudo systemctl start %s",
            service_name,
            service_name,
        )
