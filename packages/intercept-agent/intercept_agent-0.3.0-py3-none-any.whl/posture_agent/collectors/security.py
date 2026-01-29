"""Security practices collector."""

from posture_agent.collectors.base import BaseCollector, CollectorResult
from posture_agent.utils.shell import run_command


class SecurityCollector(BaseCollector):
    """Collects security configuration information."""

    name = "security"

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        security: dict[str, object] = {}

        # Git commit signing
        try:
            gpg_sign = await run_command("git", "config", "--global", "commit.gpgsign")
            security["git_signing_enabled"] = gpg_sign is not None and gpg_sign.strip().lower() == "true"

            sign_format = await run_command("git", "config", "--global", "gpg.format")
            security["git_signing_format"] = sign_format.strip() if sign_format else "gpg"
        except Exception as e:
            security["git_signing_enabled"] = False
            errors.append(f"Git signing: {e}")

        # Git user info
        try:
            git_name = await run_command("git", "config", "--global", "user.name")
            security["git_name"] = git_name.strip() if git_name else ""

            git_email = await run_command("git", "config", "--global", "user.email")
            security["git_email"] = git_email.strip() if git_email else ""
        except Exception as e:
            errors.append(f"Git user: {e}")

        # SSH keys - detect private keys by content, not just .pub files
        try:
            from pathlib import Path
            ssh_dir = Path.home() / ".ssh"
            ssh_keys: list[dict[str, str]] = []
            if ssh_dir.exists():
                for f in ssh_dir.iterdir():
                    if not f.is_file():
                        continue
                    # Skip known non-key files
                    if f.name in ("config", "known_hosts", "known_hosts.old", "authorized_keys", "environment"):
                        continue
                    if f.suffix in (".pub", ".old", ".bak", ".log"):
                        continue
                    # Check if file looks like a private key
                    try:
                        header = f.read_bytes()[:64].decode("utf-8", errors="ignore")
                        key_type = None
                        if "BEGIN OPENSSH PRIVATE KEY" in header:
                            key_type = "openssh"
                        elif "BEGIN RSA PRIVATE KEY" in header:
                            key_type = "rsa"
                        elif "BEGIN EC PRIVATE KEY" in header:
                            key_type = "ecdsa"
                        elif "BEGIN DSA PRIVATE KEY" in header:
                            key_type = "dsa"
                        if key_type:
                            # Try to determine algorithm from filename
                            algo = key_type
                            if "ed25519" in f.name:
                                algo = "ed25519"
                            elif "ecdsa" in f.name:
                                algo = "ecdsa"
                            elif "rsa" in f.name:
                                algo = "rsa"
                            elif "dsa" in f.name:
                                algo = "dsa"
                            ssh_keys.append({"name": f.name, "algorithm": algo})
                    except (OSError, PermissionError):
                        continue
            security["ssh_key_count"] = len(ssh_keys)
            security["ssh_keys"] = ssh_keys

            # Check SSH agent for loaded keys
            agent_output = await run_command("ssh-add", "-l")
            if agent_output and "no identities" not in agent_output.lower() and "error" not in agent_output.lower():
                loaded_keys = [
                    line.strip() for line in agent_output.strip().splitlines()
                    if line.strip() and not line.startswith("The agent")
                ]
                security["ssh_agent_keys"] = len(loaded_keys)
            else:
                security["ssh_agent_keys"] = 0
        except Exception as e:
            errors.append(f"SSH keys: {e}")

        # FileVault (disk encryption)
        try:
            fv_status = await run_command("fdesetup", "status")
            security["filevault_enabled"] = (
                fv_status is not None and "On" in fv_status
            )
        except Exception as e:
            security["filevault_enabled"] = False
            errors.append(f"FileVault: {e}")

        # Firewall
        try:
            fw_status = await run_command(
                "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"
            )
            security["firewall_enabled"] = (
                fw_status is not None and "enabled" in fw_status.lower()
            )
        except Exception as e:
            security["firewall_enabled"] = False
            errors.append(f"Firewall: {e}")

        # Pre-commit hooks (global)
        try:
            hooks_path = await run_command("git", "config", "--global", "core.hooksPath")
            security["global_hooks_path"] = hooks_path.strip() if hooks_path else ""
        except Exception as e:
            errors.append(f"Hooks path: {e}")

        # Git credential helper (shows secure credential management)
        try:
            # Check effective value (system + global + local), not just global
            cred_helper = await run_command("git", "config", "credential.helper")
            security["credential_helper"] = cred_helper.strip() if cred_helper else ""
        except Exception as e:
            errors.append(f"Credential helper: {e}")

        # Allowed signers (SSH signing verification)
        try:
            from pathlib import Path
            allowed_signers = await run_command("git", "config", "--global", "gpg.ssh.allowedSignersFile")
            signers_path = allowed_signers.strip() if allowed_signers else ""
            security["allowed_signers_configured"] = bool(signers_path)
            if signers_path:
                expanded = Path(signers_path).expanduser()
                security["allowed_signers_exists"] = expanded.exists()
            else:
                security["allowed_signers_exists"] = False
        except Exception as e:
            security["allowed_signers_configured"] = False
            errors.append(f"Allowed signers: {e}")

        # SSH agent type (1Password, Secretive, Apple Keychain, standard)
        try:
            from pathlib import Path
            ssh_auth_sock = await run_command("printenv", "SSH_AUTH_SOCK")
            sock_path = ssh_auth_sock.strip() if ssh_auth_sock else ""
            if "1password" in sock_path.lower() or "1Password" in sock_path:
                security["ssh_agent_type"] = "1Password"
            elif "secretive" in sock_path.lower():
                security["ssh_agent_type"] = "Secretive"
            elif "com.apple.launchd" in sock_path:
                security["ssh_agent_type"] = "Apple Keychain"
            elif sock_path:
                security["ssh_agent_type"] = "standard"
            else:
                security["ssh_agent_type"] = "none"
        except Exception as e:
            security["ssh_agent_type"] = "unknown"
            errors.append(f"SSH agent type: {e}")

        # Gatekeeper status (macOS app security)
        try:
            gk_status = await run_command("spctl", "--status")
            security["gatekeeper_enabled"] = (
                gk_status is not None and "enabled" in gk_status.lower()
            )
        except Exception as e:
            security["gatekeeper_enabled"] = False
            errors.append(f"Gatekeeper: {e}")

        return CollectorResult(
            collector=self.name,
            data=security,
            errors=errors,
        )
