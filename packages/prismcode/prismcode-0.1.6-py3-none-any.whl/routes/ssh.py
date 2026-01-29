"""
SSH connection and browsing routes.
"""
import os
import re
from flask import Blueprint, request, jsonify

from core.filesystem import SSHFileSystem, SSHConnectionError, SSHAuthenticationError

ssh_bp = Blueprint('ssh', __name__)


@ssh_bp.route('/api/ssh/hosts')
def api_ssh_hosts():
    """Get SSH hosts from ~/.ssh/config."""
    ssh_config_path = os.path.expanduser('~/.ssh/config')
    hosts = []

    try:
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, 'r') as f:
                content = f.read()

            current_host = None
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                host_match = re.match(r'^Host\s+(\S+)$', line, re.IGNORECASE)
                if host_match:
                    host_name = host_match.group(1)
                    if host_name != '*':
                        current_host = {'name': host_name, 'hostname': None, 'user': None, 'port': 22}
                        hosts.append(current_host)
                    else:
                        current_host = None
                    continue

                if current_host:
                    if line.lower().startswith('hostname'):
                        current_host['hostname'] = line.split(None, 1)[1] if len(line.split()) > 1 else None
                    elif line.lower().startswith('user'):
                        current_host['user'] = line.split(None, 1)[1] if len(line.split()) > 1 else None
                    elif line.lower().startswith('port'):
                        try:
                            current_host['port'] = int(line.split()[1])
                        except (IndexError, ValueError):
                            pass
    except Exception as e:
        print(f"Error reading SSH config: {e}")

    return jsonify({'hosts': hosts})


@ssh_bp.route('/api/ssh/parse', methods=['POST'])
def api_ssh_parse():
    """Parse an SSH command string like 'ssh -p 3333 user@host'."""
    data = request.json
    command = data.get('command', '').strip()

    if command.lower().startswith('ssh '):
        command = command[4:].strip()

    result = {'host': '', 'user': '', 'port': 22}

    port_match = re.search(r'-p\s*(\d+)', command)
    if port_match:
        result['port'] = int(port_match.group(1))
        command = re.sub(r'-p\s*\d+', '', command).strip()

    if '@' in command:
        parts = command.split('@')
        result['user'] = parts[0].strip()
        result['host'] = parts[1].split()[0].strip() if parts[1] else ''
    else:
        result['host'] = command.split()[0] if command else ''

    return jsonify(result)


@ssh_bp.route('/api/ssh/test', methods=['POST'])
def api_test_ssh():
    """Test SSH connection."""
    data = request.json
    host = data.get('host', '').strip()
    user = data.get('user', '').strip()
    port = int(data.get('port', 22))

    if not host:
        return jsonify({"success": False, "error": "Host is required"})
    if not user:
        return jsonify({"success": False, "error": "Username is required"})

    try:
        ssh_fs = SSHFileSystem(
            host=host,
            root="/tmp",
            user=user,
            port=port
        )

        ssh_fs.ls(".")
        ssh_fs.close()

        return jsonify({"success": True, "message": "Connection successful"})

    except SSHAuthenticationError as e:
        return jsonify({"success": False, "error": f"Authentication failed: {e}"})
    except SSHConnectionError as e:
        return jsonify({"success": False, "error": f"Connection failed: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@ssh_bp.route('/api/ssh/browse', methods=['POST'])
def api_ssh_browse():
    """Browse folders on a remote SSH server."""
    data = request.json
    host = data.get('host', '').strip()
    user = data.get('user', '').strip()
    port = int(data.get('port', 22))
    path = data.get('path', '~').strip()

    if not host or not user:
        return jsonify({"success": False, "error": "Host and user required"})

    try:
        if path == '~' or path.startswith('~/'):
            path = f"/home/{user}" + path[1:] if path != '~' else f"/home/{user}"

        ssh_fs = SSHFileSystem(
            host=host,
            root=path,
            user=user,
            port=port
        )

        items = ssh_fs.ls(".")
        ssh_fs.close()

        folders = []
        for item in items:
            if item.get('is_dir'):
                folders.append({
                    'name': item['name'],
                    'path': f"{path}/{item['name']}".replace('//', '/'),
                    'is_dir': True
                })

        return jsonify({
            "success": True,
            "path": path,
            "contents": folders
        })

    except SSHAuthenticationError as e:
        return jsonify({"success": False, "error": "Authentication failed"})
    except SSHConnectionError as e:
        return jsonify({"success": False, "error": "Connection failed"})
    except FileNotFoundError:
        return jsonify({"success": False, "error": f"Path not found: {path}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
