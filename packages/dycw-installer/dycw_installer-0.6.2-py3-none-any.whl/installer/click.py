from __future__ import annotations

from click import Tuple, option
from utilities.click import Str

logger_option = option("--logger", type=Str(), default="installer", help="Logger name")
ssh_option = option("--ssh", type=Str(), default=None, help="SSH user & hostname")
sudo_option = option("--sudo", is_flag=True, default=False, help="Run as 'sudo'")
retry_option = option("--retry", type=Tuple([int, int]), default=None, help="SSH retry")


__all__ = ["logger_option", "retry_option", "ssh_option", "sudo_option"]
