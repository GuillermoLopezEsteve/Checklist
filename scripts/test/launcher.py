import sys
import yaml
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "..\..\class")

sys.path.append(lib_path)

try:
    from server import Server
except ImportError:
    print(f"Error: Could not find server.py in {lib_path}")
    sys.exit(1)


def checkUrls(server):
    print(f"┌── Checking Server: {server.name} ({server.hostname})")
    
    def print_status(label, port, is_up):
        status_icon = "[\033[92mOK\033[0m]" if is_up else "[\033[91mFAIL\033[0m]" # Green OK, Red FAIL
        print(f"│   ├── {label} (Port {port}):\t{status_icon}")
    status_1 = server.check_web_status(server.web_port)
    print_status("Web Primary", server.web_port, status_1)
    status_2 = server.check_web_status(server.web_port_2)
    print_status("Web Secondary", server.web_port_2, status_2)
    
    print("└───────────────────────────────────────\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 launcher.py config.yaml")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # 1. Extract the list of server data from YAML
        # Note: Using 'enviroment' as spelled in your specific YAML
        server_list = config.get("enviroment", {}).get("servers", [])

        # 2. Create the dictionary: Key = Server Name, Value = Server Object
        server_dict = {
            item.get("name"): Server(item) 
            for item in server_list
        }

        # Debug Output
        print(f"Successfully loaded {len(server_dict)} servers into dictionary:")
        print(server_dict)

        # Iterate and Check
        print("\n--- Starting Network Connectivity Checks ---\n")
        for name, server_obj in server_dict.items():
            checkUrls(server_obj)

    except FileNotFoundError:
        print(f"Error: File '{config_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()