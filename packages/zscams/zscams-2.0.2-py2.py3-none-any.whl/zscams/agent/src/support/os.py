import sys
import subprocess

from zscams.agent.src.support.logger import get_logger

from .filesystem import write_to_file

logger = get_logger("os_support")


def is_linux():
    if sys.platform.startswith("linux"):
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


def create_system_user(username: str):
    if not is_linux():
        logger.error(
            "Error creating system user: This script is intended to run on Linux systems."
        )
        return

    if not username:
        logger.error("Error creating system user: Username must be provided.")
        return

    if system_user_exists(username):
        logger.warning("User '%s' already exists.", username)
        return

    try:
        subprocess.run(["sudo", "useradd","-m", "-s", "/bin/bash", username], check=True)
        logger.info("System user '%s' created successfully.", username)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to create user '%s': %s", username, e)


def install_systemd_service(service_name: str, content: str):
    if not is_linux():
        logger.error(
            "Error installing systemd service: This script is intended to run on Linux systems."
        )
        return

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
