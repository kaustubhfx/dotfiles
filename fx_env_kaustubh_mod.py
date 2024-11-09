import shutil
import os
import glob
import argparse
from datetime import datetime
import logging

# ==============================================
# ASCII ART HOUDINI HEADER (ADD YOUR ASCII ART HERE)
# ==============================================
HOUDINI_ASCII = '''
██╗  ██╗ ██████╗ ██╗   ██╗██████╗ ██╗███╗   ██╗██╗    ██╗██╗██╗
██║  ██║██╔═══██╗██║   ██║██╔══██╗██║████╗  ██║██║    ██║██║██║
███████║██║   ██║██║   ██║██║  ██║██║██╔██╗ ██║██║    ██║██║██║
██╔══██║██║   ██║██║   ██║██║  ██║██║██║╚██╗██║██║    ╚═╝╚╝╚╝
██║  ██║╚██████╔╝╚██████╔╝██████╔╝██║██║ ╚████║██║    ██╗██╗██╗
╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝    ╚═╝╚═╝╚═╝
'''

# ==============================================
# DEFAULTS - START
# ==============================================

# Set default Houdini version
HFS = "20.5.370"  # Default Houdini version (can be changed via args)

# Get the Houdini project and files directories from the environment variables
PROJECT_DIR = os.getenv('HOUDINI_PROJECT_DIR')
FILES_DIR = os.getenv('HOUDINI_FILES_DIR')

if not PROJECT_DIR:
    raise EnvironmentError("Environment variable HOUDINI_PROJECT_DIR is not set. Please export it in your .bash_env_variables.")

if not FILES_DIR:
    raise EnvironmentError("Environment variable HOUDINI_FILES_DIR is not set. Please export it in your .bash_env_variables.")

# User for your PC
STUDENTNAME = os.getenv('USER')

# ==============================================
# LOGGING SETUP
# ==============================================

logging.basicConfig(filename=os.path.join(FILES_DIR, 'houdini_script.log'), level=logging.INFO)

# ==============================================
# ARGUMENT PARSER SETUP
# ==============================================

parser = argparse.ArgumentParser(description="Houdini Project Manager with backup, restore, and enhanced project management")
parser.add_argument("-hv", "--hversion", help="Override Houdini version (e.g., -hv 19.5.303)", type=str)
parser.add_argument("-d", "--debug", help="Enable debugging info", action="store_true")
parser.add_argument("--backup", help="Create a backup of the current project's *.hip files", action="store_true")
parser.add_argument("--restore", help="Restore *.hip files from a specific backup timestamp", type=str)
parser.add_argument("--interactive", help="Start interactive project management mode", action="store_true")
parser.add_argument("--backup_dir", help="Specify custom directory for backups", type=str)
args = parser.parse_args()  # Parse the command-line arguments

# ==============================================
# HELPER FUNCTIONS FOR COLOR PRINTING
# ==============================================
def print_green(text):
    print(f"\033[92m{text}\033[0m")  # Green text

def print_red(text):
    print(f"\033[91m{text}\033[0m")  # Red text

def print_yellow(text):
    print(f"\033[93m{text}\033[0m")  # Yellow text

def print_black(text):
    print(f"\033[30m{text}\033[0m")  # Black text

def print_ascii_header():
    print_green(HOUDINI_ASCII)

# ==============================================
# HELPER FUNCTIONS FOR FILE AND DIRECTORY OPERATIONS
# ==============================================
def ensure_directory_exists(directory):
    """Ensure the given directory exists; create it if it doesn't."""
    if not os.path.isdir(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")
        print_yellow(f"Directory created: {directory}")

def handle_error(message):
    """Handle and log errors."""
    logging.error(message)
    print_red(message)

def check_permissions(directory):
    """Check if the script has write permissions for the given directory."""
    if not os.access(directory, os.W_OK):
        handle_error(f"No write permissions for directory: {directory}")
        return False
    return True

# ==============================================
# CREATE DIRECTORIES AND SYMLINKS
# ==============================================


def ensure_directories_and_symlinks(project_name):
    """Create necessary directories for the project and create a symbolic link named 'GEO' in HOUDINI_FILES_DIR, pointing to GEO in HOUDINI_PROJECT_DIR."""
    required_dirs = ['HIP', 'REF', 'RENDER', 'COMP']  # Directories to be created

    # Create project directory in HOUDINI_FILES_DIR
    project_path = os.path.join(FILES_DIR, project_name)
    ensure_directory_exists(project_path)

    # Create required subdirectories in uppercase
    for dir_name in required_dirs:
        dir_path = os.path.join(project_path, dir_name)
        ensure_directory_exists(dir_path)

    # Create GEO directory in HOUDINI_PROJECT_DIR under the current project name
    geo_dir_path_project = os.path.join(PROJECT_DIR, project_name, 'GEO')
    ensure_directory_exists(geo_dir_path_project)

    # Create FLIP directory inside the current project directory
    flip_dir_path = os.path.join(project_path, 'FLIP')
    ensure_directory_exists(flip_dir_path)

    # Create symbolic link named 'GEO' in HOUDINI_FILES_DIR pointing to GEO in HOUDINI_PROJECT_DIR
    symlink_path = os.path.join(project_path, 'GEO')
    if not os.path.islink(symlink_path):
        os.symlink(geo_dir_path_project, symlink_path)
        print_green(f"Created symbolic link '{symlink_path}' pointing to '{geo_dir_path_project}'")
    else:
        print_yellow(f"Symbolic link already exists: {symlink_path}")

    # Set environment variables
    os.environ['PROJECT_NAME'] = project_name
    os.environ['PROJECT_PATH'] = project_path
    print_green(f"Environment variables set for project '{project_name}'.")





# ==============================================
# HOUDINI VERSION DETECTION AND ENVIRONMENT SETTING
# ==============================================
def find_houdini_version(hversion):
    """Check if the specified Houdini version is installed."""
    houdini_base_dir = "/opt"
    houdini_install_path = os.path.join(houdini_base_dir, f"hfs{hversion}")
    if os.path.exists(houdini_install_path):
        print_green(f"Houdini version {hversion} found at {houdini_install_path}")
        return houdini_install_path
    else:
        print_red(f"Houdini version {hversion} not found!")
        return None

def set_houdini_environment(hversion):
    """Set the environment variables for Houdini."""
    houdini_path = find_houdini_version(hversion)
    if houdini_path:
        os.environ['HFS'] = houdini_path
        os.environ['HOUDINI_PATH'] = f"{houdini_path}/houdini"
        print_green(f"Environment set for Houdini {hversion}")
    else:
        handle_error(f"Failed to set environment for Houdini {hversion}")
        exit(1)

# ==============================================
# PROJECT MANAGEMENT AND SELECTION
# ==============================================
def list_recent_projects(show_all=False):
    """List recent projects based on their access time."""
    if not os.path.exists(FILES_DIR):
        handle_error(f"Directory {FILES_DIR} does not exist.")
        return []

    projects = [name for name in os.listdir(FILES_DIR) if os.path.isdir(os.path.join(FILES_DIR, name))]
    if not projects:
        print_yellow("No projects found in FILES_DIR.")
        return []

    # Sort projects based on last access time
    projects = sorted(projects, key=lambda x: os.path.getatime(os.path.join(FILES_DIR, x)), reverse=True)

    # Show only the last 6 projects unless user opts to show all
    if not show_all:
        projects = projects[:6]

    print_green("Recent Projects:" if not show_all else "All Projects:")
    for idx, project in enumerate(projects, start=1):
        last_accessed = datetime.fromtimestamp(os.path.getatime(os.path.join(FILES_DIR, project))).strftime('%B %d, %Y %I:%M %p')
        spacing = 40 - len(project)

        # Print project number with leading zero, project name, and access time
        print(f"\033[92m{idx:02d} - {project}{' ' * spacing}\033[0m", end="")
        print(f"\033[37m{last_accessed}\033[0m")  # Changed to light gray (or use \033[97m for white)
    
    return projects


def display_directory_sizes(project_path):
    """Display sizes of all directories within the selected project."""
    print_yellow(f"\nDirectory sizes inside {project_path}:\n")

    if not os.path.exists(project_path):
        handle_error(f"Project directory '{project_path}' does not exist.")
        return

    total_size = 0
    directory_sizes = {}  # Dictionary to hold directory names and their sizes

    # List all directories in the project path
    for directory in os.listdir(project_path):
        dirpath = os.path.join(project_path, directory)
        if os.path.isdir(dirpath):
            # Calculate directory size
            dir_size = sum(
                os.path.getsize(os.path.join(dirpath, f))
                for dirpath, dirnames, filenames in os.walk(dirpath)
                for f in filenames
            )
            directory_sizes[directory] = dir_size  # Store the size
            total_size += dir_size

    # Calculate the maximum length for directory names for alignment
    max_name_length = max(len(name) for name in directory_sizes.keys()) if directory_sizes else 0

    # Display sizes with equal spacing
    print_green(f"{'Directory':<{max_name_length}}  {'Size (MB)':>12}")  # Header
    print_green('-' * (max_name_length + 15))  # Divider

    for directory, size in directory_sizes.items():
        print_green(f"{directory:<{max_name_length}}  {size / (1024 * 1024):>12.2f}")  # Aligning names and sizes

    # Display the total size of the project
    print_green(f"\nTotal Project Size (for all directories): {total_size / (1024 * 1024):.2f} MB\n")

def select_project():
    """Let the user select a project or create a new one."""
    projects = list_recent_projects()

    # Prompt the user to select a project or create a new one
    choice = input("Press 'a' to show all projects, select project number, or '0' to create new: ").strip().lower()

    if choice == 'a':
        projects = list_recent_projects(show_all=True)
        choice = input("Select project number or '0' to create new: ").strip().lower()

    if choice == '0':
        project_name = input("Enter the name of the new project: ").strip()
        if project_name:
            # Ensure directories for the new project are created
            ensure_directories_and_symlinks(project_name)
            print_green(f"Created new project: {project_name}")
        else:
            handle_error("Invalid project name.")
            return select_project()  # Try again
    elif choice.isdigit() and 1 <= int(choice) <= len(projects):
        project_name = projects[int(choice) - 1]  # Assign the selected project name
        print_green(f"Selected project: {project_name}")
    else:
        handle_error("Invalid choice.")
        return select_project()  # Try again

    # Set the current project environment variable
    os.environ['CURRENT_PROJECT'] = project_name
    print_green(f"Current project set to: {os.environ['CURRENT_PROJECT']}")

    return project_name  # Ensure project_name is returned correctly

    # Set the current project environment variable
    os.environ['CURRENT_PROJECT'] = project_name
    print_green(f"Current project set to: {os.environ['CURRENT_PROJECT']}")

    return project_name  # Ensure project_name is returned



# ==============================================
# TERMINAL CUSTOMIZATION SUPPORT
# ==============================================
def customize_terminal(project_name, hfs_version):
    # Set terminal title
    os.system(f"echo -ne '\\033]0;{project_name} - Houdini {hfs_version}\\007'")

    # Customize prompt color and content
    custom_prompt = f'PS1="{project_name} ({hfs_version})$ "'
    os.system(f'export {custom_prompt}')

# ==============================================
# BACKUP AND RESTORE HANDLING
# ==============================================
def create_backup(project_dir, backup_dir=None):
    """Create a backup of *.hip files."""
    if backup_dir is None:
        backup_dir = os.path.join(project_dir, 'BACKUPS')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(backup_dir, timestamp)
    ensure_directory_exists(backup_dir)
    
    # Find and copy *.hip files to backup directory
    hip_files = glob.glob(os.path.join(project_dir, '*.hip'))
    if not hip_files:
        print_red("No .hip files found for backup.")
        return
    
    for file in hip_files:
        shutil.copy(file, backup_dir)
        print_green(f"Backed up {file} to {backup_dir}")

def restore_backup(project_dir, timestamp):
    """Restore a specific backup based on timestamp."""
    backup_dir = os.path.join(project_dir, 'BACKUPS', timestamp)
    
    if not os.path.exists(backup_dir):
        handle_error(f"No backup found for the specified timestamp: {timestamp}")
        return
    
    restore_dir = os.path.join(project_dir, f'RESTORED_{timestamp}')
    ensure_directory_exists(restore_dir)
    
    hip_files = glob.glob(os.path.join(backup_dir, '*.hip'))
    if not hip_files:
        handle_error("No .hip files found in the backup.")
        return
    
    for file in hip_files:
        shutil.copy(file, restore_dir)
        print_green(f"Restored {file} to {restore_dir}")

# ==============================================
# INTERACTIVE MODE FOR PROJECT MANAGEMENT
# ==============================================
def interactive_mode():
    project_name = None  # Initialize project_name as None

    while True:
        print_yellow("\n--- Interactive Mode ---")
        print("1 - Select or Create Project")
        print("2 - Create Backup")
        print("3 - Restore Backup")
        print("4 - Exit")

        choice = input("Select an option: ")

        if choice == '1':
            project_name = select_project()  # This will return the project name
            print_green(f"Selected project: {project_name}")
        elif choice == '2':
            if project_name:
                create_backup(os.path.join(FILES_DIR, project_name))  # Pass the correct project path
            else:
                print_red("No project selected.")
        elif choice == '3':
            if project_name:
                timestamp = input("Enter the backup timestamp to restore: ")
                restore_backup(os.path.join(FILES_DIR, project_name), timestamp)  # Pass the correct project path
            else:
                print_red("No project selected.")
        elif choice == '4':
            print_green("Exiting Interactive Mode.")
            break
        else:
            print_red("Invalid choice, please try again.")

    # After exiting the loop, launch the xterm window for the project
    if project_name:
        customize_terminal(project_name, HFS)
        launch_xterm_with_env(project_name, HFS)
    else:
        print_red("No project selected. Cannot launch xterm.")



# ==============================================
# XTERM FUNCTIONALITY TO LAUNCH TERMINAL
# ==============================================
def launch_xterm_with_env(project_name, hfs_version):
    """Launch an xterm window with Houdini environment settings."""

    # Prepare environment variables
    houdini_setup = f"""
export HFS="/opt/hfs{hfs_version}";
export HOUDINI_PATH="$HFS/houdini;&";
export PROJECT_NAME="{project_name}";
export PROJECT_PATH="{FILES_DIR}/{project_name}";
export COMP="$PROJECT_PATH/COMP";
export FLIP="$PROJECT_PATH/FLIP";
export GEO="$PROJECT_PATH/GEO";
export HIP="$PROJECT_PATH/HIP";
export REF="$PROJECT_PATH/REF";
export RENDER="$PROJECT_PATH/RENDER";
export JOB="$PROJECT_PATH";
cd $PROJECT_PATH;
"""

    # Write the environment setup to a temporary file
    temp_env_file = "/tmp/fx_env_xterm.env"
    with open(temp_env_file, "w") as env_file:
        env_file.write(houdini_setup)

    # Launch xterm with the custom environment
    title = f"{project_name} - Houdini {hfs_version}"
    xterm_cmd = f"xterm -title '{title}' -hold -e 'source {temp_env_file}; /bin/bash' &"
    
    os.system(xterm_cmd)
    print_green(f"Launched xterm for project '{project_name}' with Houdini {hfs_version}.")

# ==============================================
# MAIN LOGIC
# ==============================================
print_ascii_header()

# Set up Houdini environment
print(f"Setting up environment for Houdini {HFS}")
if args.hversion:
    set_houdini_environment(args.hversion)

project_name = select_project()
print(f"Working on project: {project_name}")

# Customize terminal
customize_terminal(os.environ['CURRENT_PROJECT'], HFS)

# Handle backup or restore if specified in arguments
if args.backup:
    create_backup(os.path.join(FILES_DIR, project_name))
elif args.restore:
    restore_backup(os.path.join(FILES_DIR, project_name), args.restore)

# Start interactive mode if requested
if args.interactive:
    interactive_mode()

# Inform the user the project is ready and then launch xterm
print(f"Project '{os.environ['CURRENT_PROJECT']}' is ready. You can start working in Houdini now!")

# Launch xterm with environment variables set
launch_xterm_with_env(project_name, HFS)
