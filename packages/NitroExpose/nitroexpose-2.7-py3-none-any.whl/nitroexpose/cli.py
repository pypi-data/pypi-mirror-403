import os  
import subprocess  
import sys  
import re  
import termios  
import tty  
import select  
import time  
import requests  
import signal  
import socket  
import ssl  
import importlib.metadata
import random
import string

# cli.py (Main File)  
# 𝗠𝗮𝗻𝗮𝗴𝗲𝗱 𝗕𝘆 @Nactire  

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    banner = """
 ███╗   ██╗██╗████████╗██████╗  ██████╗ 
 ████╗  ██║██║╚══██╔══╝██╔══██╗██╔═══██╗
 ██╔██╗ ██║██║   ██║   ██████╔╝██║   ██║
 ██║╚██╗██║██║   ██║   ██╔══██╗██║   ██║
 ██║ ╚████║██║   ██║   ██║  ██║╚██████╔╝
 ╚═╝  ╚═══╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ 
        ███████╗██╗  ██╗██████╗  ██████╗ ███████╗███████╗
        ██╔════╝╚██╗██╔╝██╔══██╗██╔═══██╗██╔════╝██╔════╝
        █████╗   ╚███╔╝ ██████╔╝██║   ██║███████╗█████╗
        ██╔══╝   ██╔██╗ ██╔═══╝ ██║   ██║╚════██║██╔══╝
        ███████╗██╔╝ ██╗██║     ╚██████╔╝███████║███████╗
        ╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚══════╝
    """

    for line in banner.splitlines():
        print_red(line)
        time.sleep(0.025)

    print()
    typing_effect("  Domain Exposure Tool with SSL Automation", 0.03)
    print()
    version = get_version()
    typing_effect(f"  Version {version}  |  Managed by @lieqy", 0.02)
    print("\n")

def typing_effect(text, delay=0.05):
    for char in text:
        sys.stdout.write("\033[1;33m" + char + "\033[0m")
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_animation(text, duration=1.5):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    
    while time.time() < end_time:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r\033[38;2;0;255;234m{frame} {text}\033[0m")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    
    sys.stdout.write(f"\r\033[1;32m✓ {text}\033[0m\n")
    sys.stdout.flush()

def progress_bar(text, steps=20):
    print_turquoise(f"\n{text}")
    bar_length = 50
    
    for i in range(steps + 1):
        filled = int(bar_length * i / steps)
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = int(100 * i / steps)
        
        sys.stdout.write(f"\r\033[38;2;0;255;234m[{bar}] {percent}%\033[0m")
        sys.stdout.flush()
        time.sleep(0.05)
    
    print("\n")
  
def print_green(text):  
    print("\033[1;32m" + text + "\033[0m")  
  
def print_red(text):  
    print("\033[1;31m" + text + "\033[0m")  
      
def print_yellow(text):  
    print("\033[1;33m" + text + "\033[0m")  
      
def print_turquoise(text):  
    print("\033[38;2;0;255;234m" + text + "\033[0m")

def print_highlighted_turquoise(text):
    print("\033[1;48;2;0;255;234;30m" + text + "\033[0m")
    
def print_mixed(text):
    reset = "\033[0m"

    r1, g1, b1 = 0, 255, 0

    r2, g2, b2 = 71, 255, 203

    length = max(len(text) - 1, 1)
    output = ""

    for i, ch in enumerate(text):
        r = int(r1 + (r2 - r1) * i / length)
        g = int(g1 + (g2 - g1) * i / length)
        b = int(b1 + (b2 - b1) * i / length)

        output += f"\033[38;2;{r};{g};{b}m{ch}"

    print(output + reset)

def print_box(text, color="turquoise"):
    """Print text in a box"""
    width = len(text) + 4
    if color == "turquoise":
        print("\033[38;2;0;255;234m╔" + "═" * width + "╗\033[0m")
        print("\033[38;2;0;255;234m║  " + text + "  ║\033[0m")
        print("\033[38;2;0;255;234m╚" + "═" * width + "╝\033[0m")
    elif color == "green":
        print("\033[1;32m╔" + "═" * width + "╗\033[0m")
        print("\033[1;32m║  " + text + "  ║\033[0m")
        print("\033[1;32m╚" + "═" * width + "╝\033[0m")
      
def get_version():  
    try:  
        version = importlib.metadata.version('nitroexpose')  
        return version  
    except importlib.metadata.PackageNotFoundError:  
        return "Unknown"  
  
def run_command(cmd):  
    process = subprocess.Popen(  
        cmd,   
        shell=True,  
        stdout=subprocess.DEVNULL,  
        stderr=subprocess.DEVNULL  
    )  
    process.wait()  
    return process.returncode  
  
def is_installed(cmd):  
    return subprocess.call(  
        f"{cmd} > /dev/null 2>&1",   
        shell=True,  
        stdout=subprocess.DEVNULL,  
        stderr=subprocess.DEVNULL  
    ) == 0  
      
def is_certbot_nginx_plugin_installed():  
    try:  
        result = subprocess.check_output(  
            "dpkg -l | grep python3-certbot-nginx",   
            shell=True,   
            text=True,  
            stderr=subprocess.DEVNULL  
        )  
        return "python3-certbot-nginx" in result  
    except subprocess.CalledProcessError:  
        return False

def is_supervisor_installed():
    try:
        result = subprocess.check_output(
            "dpkg -l | grep supervisor",
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL
        )
        return "supervisor" in result
    except subprocess.CalledProcessError:
        return False
  
def is_port_listening(port):  
    try:  
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        sock.settimeout(2)  
        result = sock.connect_ex(('127.0.0.1', int(port)))  
        sock.close()  
        return result == 0  
    except Exception:  
        return False  
  
def check_ssl_certificate(domain, port=443, timeout=10):  
    try:  
        context = ssl.create_default_context()  
          
        with socket.create_connection((domain, port), timeout=timeout) as sock:  
            with context.wrap_socket(sock, server_hostname=domain) as ssock:  
                cert = ssock.getpeercert()  
                  
                if cert:  
                    return True  
                return False  
                  
    except ssl.SSLError as e:  
        return False  
    except socket.timeout:  
        return False  
    except socket.gaierror:  
        return False  
    except ConnectionRefusedError:  
        return False  
    except Exception as e:  
        return False  
  
def restricted_input(prompt, allowed_pattern):  
    def handle_sigint(signum, frame):  
        print("\n\n")  
        sys.exit(1)  
  
    signal.signal(signal.SIGINT, handle_sigint)  
  
    sys.stdout.write("\033[1;32m" + prompt + "\033[0m")  
    sys.stdout.flush()  
  
    fd = sys.stdin.fileno()  
    old_settings = termios.tcgetattr(fd)  
    tty.setraw(fd)  
  
    buffer = ""  
    try:  
        while True:  
            r, _, _ = select.select([fd], [], [], 0)  
            if r:  
                ch = sys.stdin.read(1)  
                if ch == "\n" or ch == "\r":  
                    print()  
                    break  
                elif ch == "\x03":  
                    raise KeyboardInterrupt  
                elif ch == "\x7f":  
                    if buffer:  
                        buffer = buffer[:-1]  
                        sys.stdout.write("\b \b")  
                        sys.stdout.flush()  
                elif re.match(allowed_pattern, ch):  
                    buffer += ch  
                    sys.stdout.write(ch)  
                    sys.stdout.flush()  
    except KeyboardInterrupt:  
        print("\n\n")  
        sys.exit(1)  
    finally:  
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  
    return buffer

def show_menu():
    options = [
        "Your Own Domain/Subdomainㅤ",
        "Free Subdomainㅤ"
    ]
    selected = 0
    
    def handle_sigint(signum, frame):
        print("\n\n")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, handle_sigint)
    
    print_turquoise("╔════════════════════════════════════════════════╗")
    print_turquoise("║     Select Your Configuration Option           ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setcbreak(fd)

        for i, option in enumerate(options):
            if i == selected:
                print_highlighted_turquoise(f"  ➜ {option}")
            else:
                print_turquoise(f"    {option}")
        
        while True:
            ch = sys.stdin.read(1)
            
            if ch == '\x1b':
                next1, next2 = sys.stdin.read(2)
                if next1 == '[':
                    if next2 == 'A':  # Up arrow
                        selected = (selected - 1) % len(options)
                    elif next2 == 'B':  # Down arrow
                        selected = (selected + 1) % len(options)

                    sys.stdout.write(f"\033[{len(options)}A")
                    for i, option in enumerate(options):
                        sys.stdout.write("\033[2K")
                        if i == selected:
                            print_highlighted_turquoise(f"  ➜ {option}")
                        else:
                            print_turquoise(f"    {option}")
                        
            elif ch == '\r' or ch == '\n':  # Enter key
                break
            elif ch == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
                
    except KeyboardInterrupt:
        print("\n\n")
        sys.exit(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    print()
    return selected

def get_system_arch():
    """Detect system architecture"""
    arch = os.uname().machine.lower()
    
    arch_map = {
        'x86_64': 'cloudflared-linux-amd64',
        'amd64': 'cloudflared-linux-amd64',
        'aarch64': 'cloudflared-linux-arm64',
        'arm64': 'cloudflared-linux-arm64',
        'armv7l': 'cloudflared-linux-arm',
        'i686': 'cloudflared-linux-386',
        'i386': 'cloudflared-linux-386'
    }
    
    return arch_map.get(arch, None)

def is_cloudflared_installed():
    """Check if cloudflared is installed"""
    try:
        result = subprocess.run(
            ["cloudflared", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def install_cloudflared():
    print_yellow("Installing NitroCloudㅤ")

    arch = get_system_arch()
    if not arch:
        print_red("\n✗ Unsupported architecture For NitroCloud installation.ㅤ\n")
        return False
    
    loading_animation(f"Detecting System Architectureㅤ", 1.5)

    home_dir = os.path.expanduser("~")
    download_path = os.path.join(home_dir, arch)

    download_url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/{arch}"
    
    try:
        loading_animation("Downloading NitroCloud...ㅤ", 2)
        response = requests.get(download_url, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print_green("✓ NitroCloud downloaded successfullyㅤ")
    except Exception as e:
        print_red(f"\n✗ Failed to download NitroCloud: {str(e)}ㅤ\n")
        return False

    try:
        loading_animation("Setting permissions...ㅤ", 1)
        run_command(f"chmod +x {download_path}")
        print_green("✓ Permissions set successfullyㅤ")
    except Exception as e:
        print_red(f"\n✗ Failed to set permissions: {str(e)}ㅤ\n")
        return False

    try:
        loading_animation("Installing to system...ㅤ", 1.5)
        run_command(f"sudo mv {download_path} /usr/local/bin/cloudflared")
        print_green("✓ NitroCloud installed to systemㅤ")
    except Exception as e:
        print_red(f"\n✗ Failed to move to /usr/local/bin: {str(e)}ㅤ\n")
        return False

    time.sleep(1)
    if is_cloudflared_installed():
        print_green("✓ NitroCloud installed successfullyㅤ")
        return True
    else:
        print_red("\n✗ There are issues in installing NitroCloud.ㅤ\n")
        return False

def generate_random_name(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_current_user():
    try:
        result = subprocess.check_output("whoami", shell=True, text=True)
        return result.strip()
    except Exception:
        return "root"

def extract_cloudflare_url(log_file, timeout=20):
    pattern = r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com'
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                match = re.search(pattern, content)
                if match:
                    return match.group(0)
        except FileNotFoundError:
            pass
        
        time.sleep(0.5)
    
    return None

def handle_free_subdomain():
    print_turquoise("\n╔════════════════════════════════════════════════╗")
    print_turquoise("║     Checking NitroCloud Dependencies...       ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
    
    if is_cloudflared_installed():
        print_green("✓ NitroCloud already installedㅤ")
    else:
        if not install_cloudflared():
            sys.exit(1)

    if is_supervisor_installed():
        print_green("✓ Supervisor already installedㅤ")
    else:
        install_and_verify_package(
            "Supervisor",
            is_supervisor_installed,
            [
                "sudo apt update -y && sudo apt upgrade -y && sudo apt install supervisor -y"
            ]
        )
    
    print("\n")
    print_turquoise("╔════════════════════════════════════════════════╗")
    print_turquoise("║    Port Configurationㅤ                        ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
    
    print_turquoise("┌─╼ Enter Port To Exposeㅤ")
    port = restricted_input("\033[38;2;0;255;234m└────╼ ❯❯❯ \033[0m", r"[0-9]+")
    
    print("\n")
    
    if not is_port_listening(port):
        print_red("✗ Port Not Listening, Operation Failed.ㅤ")
        sys.exit(1)
    
    print_turquoise("╔════════════════════════════════════════════════╗")
    print_turquoise("║     Starting Subdomain Exposure Process...     ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")

    random_name = generate_random_name(8)
    conf_path = f"/etc/supervisor/conf.d/{random_name}.conf"
    log_out = f"/var/log/{random_name}.out.log"
    log_err = f"/var/log/{random_name}.err.log"

    current_user = get_current_user()
    home_dir = os.path.expanduser("~")

    supervisor_conf = f"""[program:{random_name}]
directory={home_dir}
command=cloudflared tunnel --url http://localhost:{port}
autostart=true
autorestart=true
stderr_logfile={log_err}
stdout_logfile={log_out}
user={current_user}
"""
    
    try:
        with open(conf_path, 'w') as f:
            f.write(supervisor_conf)
        print_green(f"✓ Supervisor configuration created: {random_name}ㅤ")
    except Exception as e:
        print_red(f"✗ Failed to create supervisor config: {str(e)}ㅤ")
        sys.exit(1)

    loading_animation("Reloading Supervisor...ㅤ", 1.5)
    run_command("sudo supervisorctl reread")
    run_command("sudo supervisorctl update")
    
    print_green("✓ Supervisor configuration reloadedㅤ")

    loading_animation("Connecting to Cloudflare Server...ㅤ", 2)
    
    extracted_url = extract_cloudflare_url(log_out, timeout=20)
    
    if not extracted_url:
        extracted_url = extract_cloudflare_url(log_err, timeout=5)
    
    if not extracted_url:
        print_red("✗ NitroCloud Trouble To Connecting Cloudflare Server.ㅤ\n")
        # Cleanup
        run_command(f"sudo supervisorctl stop {random_name}")
        run_command(f"sudo supervisorctl remove {random_name}")
        run_command(f"sudo rm -f {conf_path}")
        sys.exit(1)
    
    print("\n")
    print_mixed(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print_mixed(f"Exposed Successfully On Subdomain\n")
    print_mixed(f"Exposed On: {extracted_url}\n")
    print_mixed(f"Port: {port}\n")
    print_mixed(f"SSL Installed Using Google Trust.\n")
    print_yellow(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
    print_yellow(f"If You Like NitroExpose, Please Support Us by:\n")
    print_yellow(f" * Join Our Telegram Channel:   https://t.me/NacDevs")
    print_yellow(f" * Please Star Our Project:     https://github.com/yuvrajmodz/NitroExpose")
    print_yellow(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n\n")
    
    sys.exit(0)
  
def install_and_verify_package(package_name, check_cmd, install_cmds):  
    loading_animation(f"Installing {package_name}...ㅤ", 2)
      
    for cmd in install_cmds:  
        run_command(cmd)  
      
    if check_cmd():  
        print_green(f"✓ {package_name} installed successfullyㅤ")  
        return True  
    else:  
        print_red(f"✗ {package_name} installation failedㅤ")  
        sys.exit(1)  
  
def is_valid_domain(domain):  
    if "http://" in domain or "https://" in domain or " " in domain:  
        return False  
  
    if "." not in domain:  
        return False  
  
    pattern = r'^[a-zA-Z0-9\.\-]+$'  
    if not re.match(pattern, domain):  
        return False  
      
    return True  
  
def is_subdomain(domain):  
    parts = domain.split(".")  
    return len(parts) > 2  
  
def remove_domain(domain):  
    if os.geteuid() != 0:  
        print_red("\n✗ Please Use Root Environment.ㅤ\n")  
        sys.exit(1)  
      
    if not is_valid_domain(domain):  
        print_red("\n✗ Domain Format Not Valid.ㅤ\n")  
        sys.exit(1)  
      
    if not is_installed("nginx -v"):  
        install_and_verify_package(  
            "NGINX",  
            lambda: is_installed("nginx -v"),  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y nginx",  
                "sudo systemctl start nginx",  
                "sudo systemctl enable nginx"  
            ]  
        )  
    else:  
        print_green("✓ NGINX already installedㅤ")  
  
    if not is_installed("certbot --version"):  
        install_and_verify_package(  
            "Certbot",  
            lambda: is_installed("certbot --version"),  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y certbot python3-certbot-nginx"  
            ]  
        )  
    else:  
        print_green("✓ Certbot already installedㅤ")  
          
    if not is_certbot_nginx_plugin_installed():  
        install_and_verify_package(  
            "python3-certbot-nginx plugin",  
            is_certbot_nginx_plugin_installed,  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y python3-certbot-nginx"  
            ]  
        )  
    else:  
        print_green("✓ python3-certbot-nginx plugin already installedㅤ")  
      
    print("\n")  
      
    available_path = f"/etc/nginx/sites-available/{domain}"  
    enabled_path = f"/etc/nginx/sites-enabled/{domain}"  
      
    available_exists = os.path.exists(available_path)  
    enabled_exists = os.path.exists(enabled_path)  
      
    domain_type = "Subdomain" if is_subdomain(domain) else "Domain"  
      
    if not available_exists and not enabled_exists:  
        run_command(f"sudo rm -f {available_path}")  
        run_command(f"sudo rm -f {enabled_path}")  
        run_command("sudo systemctl reload nginx")  
        print_red(f"✗ Targeted {domain_type} Doesn't Exist in Your Server.ㅤ\n")  
        sys.exit(1)  
    elif not available_exists or not enabled_exists:  
        run_command(f"sudo rm -f {available_path}")  
        run_command(f"sudo rm -f {enabled_path}")  
        run_command("sudo systemctl reload nginx")  
        print_red(f"✗ Targeted {domain_type} Doesn't Exist in Your Server.ㅤ\n")  
        sys.exit(1)  
    else:  
        run_command(f"sudo rm -f {available_path}")  
        run_command(f"sudo rm -f {enabled_path}")  
        run_command("sudo systemctl reload nginx")  
        print_green(f"\n✓ {domain_type} Removed Successfully.ㅤ\n")  
        sys.exit(0)  
  
def main():  
    # Clear screen and show banner
    clear_screen()
    print_banner()
    
    if len(sys.argv) == 2 and sys.argv[1] in ["-v", "--v"]:  
        version = get_version()  
        print_green(f"V{version}")  
        sys.exit(0)  
  
    if len(sys.argv) == 3 and sys.argv[1] == "remove":  
        domain = sys.argv[2]  
        remove_domain(domain)  
        return  
      
    if os.geteuid() != 0:  
        print_red("\n✗ Please Use Root Environment.ㅤ\n")  
        sys.exit(1)

    selected_option = show_menu()

    if selected_option == 1:
        handle_free_subdomain()
        return

    print_turquoise("\n╔════════════════════════════════════════════════╗")
    print_turquoise("║     Checking System Dependencies...            ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
  
    if not is_installed("nginx -v"):  
        install_and_verify_package(  
            "NGINX",  
            lambda: is_installed("nginx -v"),  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y nginx",  
                "sudo systemctl start nginx",  
                "sudo systemctl enable nginx"  
            ]  
        )  
    else:  
        print_green("✓ NGINX already installedㅤ")  
  
    if not is_installed("certbot --version"):  
        install_and_verify_package(  
            "Certbot",  
            lambda: is_installed("certbot --version"),  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y certbot python3-certbot-nginx"  
            ]  
        )  
    else:  
        print_green("✓ Certbot already installedㅤ")  
  
    if not is_certbot_nginx_plugin_installed():  
        install_and_verify_package(  
            "python3-certbot-nginx plugin",  
            is_certbot_nginx_plugin_installed,  
            [  
                "sudo apt update -o Acquire::AllowInsecureRepositories=true",  
                "sudo apt install -y python3-certbot-nginx"  
            ]  
        )  
    else:  
        print_green("✓ python3-certbot-nginx plugin already installedㅤ")  
          
    print("\n")  
    print_turquoise("╔════════════════════════════════════════════════╗")
    print_turquoise("║    Domain Configurationㅤ                      ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
  
    print_turquoise("┌─╼ Enter Domain Or Subdomainㅤ")  
    domain = restricted_input("\033[38;2;0;255;234m└────╼ ❯❯❯ \033[0m", r"[a-zA-Z0-9\.\-]")  
      
    print("\n")  
      
    if "." not in domain:  
        print_red("✗ Domain is invalid, Operation Failed.ㅤ")  
        sys.exit(1)  
  
    print_turquoise("┌─╼ Enter Port To Exposeㅤ")  
    port = restricted_input("\033[38;2;0;255;234m└────╼ ❯❯❯ \033[0m", r"[0-9]+")  
      
    print("\n")  
  
    if not is_port_listening(port):  
        print_red("✗ Port Not Listening, Operation Failed.ㅤ")  
        sys.exit(1)  

    print_turquoise("╔════════════════════════════════════════════════╗")
    print_turquoise("║     Starting Domain Exposure Process...        ║")
    print_turquoise("╚════════════════════════════════════════════════╝\n")
  
    nginx_temp_conf = f"""  
server {{  
    server_name {domain};  
  
    location /nitroverify/auth.txt {{  
        default_type text/plain;  
        return 200 "nitroverify-success";  
    }}  
  
    location / {{  
        return 404;  
    }}  
  
    listen 80;  
}}  
"""  
    conf_path = f"/etc/nginx/sites-available/{domain}"  
    with open(conf_path, "w") as f:  
        f.write(nginx_temp_conf)  
  
    run_command(f"sudo ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")  
    run_command("sudo systemctl reload nginx")  
  
    loading_animation("Verifying domain configuration...ㅤ", 3)
    time.sleep(2)  
  
    verified = False  
    for url in [f"http://{domain}/nitroverify/auth.txt", f"https://{domain}/nitroverify/auth.txt"]:  
        try:  
            r = requests.get(url, timeout=5)  
            if "nitroverify-success" in r.text:  
                verified = True  
                break  
        except Exception:  
            continue  
  
    if not verified:  
        print_red("✗ Domain Verification Failed, Check Records Carefully.ㅤ")  
        run_command(f"sudo rm -f /etc/nginx/sites-available/{domain}")  
        run_command(f"sudo rm -f /etc/nginx/sites-enabled/{domain}")  
        run_command("sudo systemctl reload nginx")  
        sys.exit(1)  
  
    print_green("✓ Domain Verification Successㅤ\n")  
  
    run_command(f"sudo rm -f /etc/nginx/sites-available/{domain}")  
    run_command(f"sudo rm -f /etc/nginx/sites-enabled/{domain}")  
    run_command("sudo systemctl reload nginx")  
      
    progress_bar("Installing SSL Certificate...ㅤ", 25)
  
    nginx_conf = f"""  
server {{  
    server_name {domain};  
  
    location / {{  
        proxy_pass http://127.0.0.1:{port};  
        proxy_set_header Host $host;  
        proxy_set_header X-Real-IP $remote_addr;  
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  
        proxy_set_header X-Forwarded-Proto $scheme;  
    }}  
  
    listen 80;  
}}  
"""  
    conf_path = f"/etc/nginx/sites-available/{domain}"  
    with open(conf_path, "w") as f:  
        f.write(nginx_conf)  
  
    run_command(f"sudo ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")  
    run_command("sudo systemctl reload nginx")  
  
    run_command(f"sudo certbot --nginx -d {domain} --non-interactive --agree-tos --email nitroexpose@gmail.com")  
    run_command("sudo systemctl reload nginx")  
  
    loading_animation("Verifying SSL Certificate...ㅤ", 2)
    time.sleep(1)  
  
    ssl_installed = check_ssl_certificate(domain, port=443, timeout=10)  
  
    print("\n")
    if ssl_installed:
        print_mixed(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
        print_mixed(f"Exposed Successfully On Your Domain\n")
        print_mixed(f"Exposed On: https://{domain}\n")
        print_mixed(f"Port: {port}\n")
        print_mixed(f"SSL Installed Using Let's Encrypt.\n")
        print_yellow(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
        print_yellow(f"If You Like NitroExpose, Please Support Us by:\n")
        print_yellow(f" * Join Our Telegram Channel:   https://t.me/NacDevs")
        print_yellow(f" * Please Star Our Project:     https://github.com/yuvrajmodz/NitroExpose")
        print_yellow(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n\n")
    else:
        print_mixed(f"- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
        print_mixed(f"Exposed Successfully On Your Domain\n")
        print_mixed(f"Exposed On: http://{domain}\n")
        print_mixed(f"Port: {port}\n")
        print_yellow(f"Unfortunately, please verify your records carefully. Your server is exposed on your domain, and we are experiencing difficulties while attempting to install an SSL certificate.\n\n")
  
if __name__ == "__main__":  
    main()