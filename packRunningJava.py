# Create a runnable Java package, jars/config file/JRE are included.
# 
# Steps to use this script.
# 1) configure these 2 variables: JDK_PATH and PACK_DIR
# 2) start the Java application you 'd like to pack
# 3) run this script:  >  python packRunningJava.py
# 4) go to PACK_DIR, and double click start_program.bat


import os
import subprocess
import shutil
import re

# Configure global variables
JDK_PATH = r"d:\software\dev\jdk22" 
#MAIN_CLASS = "tcs.base.starter.SimpleStarter"
MAIN_CLASS = "com.cnnckp.tcs.tcptester.TcpTesterApplication"
PACK_DIR = "D:\\tmp\\pack2"  # Target directory for packaging
DEPENDENCY_DIR = os.path.join(PACK_DIR, "dependencies")  # Directory for dependencies
EXTRA_FILES_AND_DIRS = [
    # "D:\\codes\\cnnckp_tcs\\base\\starter\\archive",
    # "D:\\codes\\cnnckp_tcs\\base\\starter\\nfsSharedStorage",
    # "D:\\codes\\cnnckp_tcs\\base\\starter\\ois",
    # "D:\\codes\\cnnckp_tcs\\base\\starter\\persistence",
    # "D:\\codes\\cnnckp_tcs\\base\\starter\\tps_repository",
    # "D:\\codes\\cnnckp_tcs\\tcs-config"
]


# Use jlink to generate custom JRE
def generate_custom_jre():
    try:
        jlink_executable = os.path.join(JDK_PATH, "bin", "jlink.exe")  # Path to jlink
        output_jre_dir = os.path.join(PACK_DIR, "custom-jre")  # Output directory for custom JRE
        
        # Ensure output directory doesn't exist, delete if it exists
        if os.path.exists(output_jre_dir):
            print(f"Directory already exists, removing: {output_jre_dir}")
            shutil.rmtree(output_jre_dir)

        # Use java --list-modules to get all available modules
        java_executable = os.path.join(JDK_PATH, "bin", "java.exe")
        available_modules = subprocess.check_output([java_executable, "--list-modules"]).decode().strip().splitlines()

        # Extract module names (only extract the part before @, remove version numbers)
        modules_to_add = ",".join([line.split('@')[0] for line in available_modules])

        # Use jlink to generate JRE
        print(f"Generating custom JRE with all available modules at: {output_jre_dir}")
        subprocess.check_call([
            jlink_executable,
            "--module-path", os.path.join(JDK_PATH, "jmods"),
            "--add-modules", modules_to_add,
            "--output", output_jre_dir,
            "--no-header-files",
            "--no-man-pages"
        ])
        print("Custom JRE generated successfully.")
    except subprocess.CalledProcessError:
        print("Error occurred during JRE generation.")
        exit(1)



# Get information about a specific Java process
def get_java_process_info(main_class):
    try:
        process = subprocess.Popen(
            ['jcmd', main_class, 'VM.command_line'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error retrieving process info: {stderr.decode()}")
            return None

        output = stdout.decode()
        return output

    except Exception as e:
        print(f"Exception while retrieving process info: {e}")
        return None


# Parse jcmd output to extract classpath
def parse_classpath(jcmd_output):
    classpath_pattern = re.compile(r"java_class_path \(initial\): (.+)")
    match = classpath_pattern.search(jcmd_output)
    
    if match:
        classpath = match.group(1)
        return classpath.split(';')
    
    return []


# Parse jcmd output to extract JVM arguments
def parse_jvm_args(jcmd_output):
    jvm_args_pattern = re.compile(r"jvm_args: (.+)")
    match = jvm_args_pattern.search(jcmd_output)
    
    if match:
        return match.group(1)
    
    return ""


# Copy dependency files from classpath
def copy_dependencies(classpath_list, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for path in classpath_list:
        if os.path.exists(path):
            try:
                # Get drive part and convert to lowercase
                drive, tail = os.path.splitdrive(path)
                drive_letter = drive.lower().rstrip(':')

                # Construct target path, preserving the entire path structure, including drive part
                target_path = os.path.join(target_directory, drive_letter, tail.lstrip("\\"))

                if os.path.isfile(path):
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy(path, target_path)
                    print(f"Copied file: {path} -> {target_path}")
                elif os.path.isdir(path):
                    shutil.copytree(path, target_path, dirs_exist_ok=True)
                    print(f"Copied directory: {path} -> {target_path}")
            except Exception as e:
                print(f"Error copying {path}: {e}")
        else:
            print(f"Path not found: {path}")


# Copy additional directories and files
def copy_extra_files(extra_list, pack_dir):
    for item in extra_list:
        if os.path.exists(item):
            dest = os.path.join(pack_dir, os.path.basename(item))
            try:
                if os.path.isdir(item):
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                    print(f"Copied directory: {item} -> {dest}")
                elif os.path.isfile(item):
                    shutil.copy(item, dest)
                    print(f"Copied file: {item} -> {dest}")
            except Exception as e:
                print(f"Error copying {item}: {e}")
        else:
            print(f"Extra file or directory not found: {item}")


# Generate .bat file to launch Java program
def create_bat_file(main_class, classpath_list, target_directory, jvm_args=None, prog_args=None):
    classpath = ";".join([
        os.path.relpath(os.path.join(target_directory, os.path.splitdrive(p)[0].lower().rstrip(':'), os.path.splitdrive(p)[1].lstrip("\\")), start=PACK_DIR)
        for p in classpath_list
    ])
    
    # Use provided JVM arguments or fallback to default
    if not jvm_args:
        jvm_args = "--add-opens=java.desktop/java.beans=ALL-UNNAMED"
    
    # Use provided program arguments or fallback to default
    if not prog_args:
        prog_args = ["tcs-config/tcs-room1.conf", "tcs-config/tcs-global.conf", "0", "mockUcs"]
    
    # Remove any -javaagent arguments that reference IDE-specific paths
    jvm_args_parts = jvm_args.split()
    filtered_jvm_args = []
    i = 0
    while i < len(jvm_args_parts):
        if jvm_args_parts[i].startswith("-javaagent:") and ("idea_rt.jar" in jvm_args_parts[i] or "eclipse" in jvm_args_parts[i]):
            # Skip IDE-specific agent
            i += 1
        else:
            filtered_jvm_args.append(jvm_args_parts[i])
            i += 1
    
    jvm_args = " ".join(filtered_jvm_args)
    
    # Build the full Java command
    java_command = f'custom-jre\\bin\\java {jvm_args} -cp "{classpath}" {main_class}'
    
    # Add program arguments if available
    if prog_args:
        if isinstance(prog_args, list):
            java_command += f' {" ".join(prog_args)}'
        else:
            java_command += f' {prog_args}'
    
    output_bat = os.path.join(PACK_DIR, "start_program.bat")

    with open(output_bat, 'w') as f:
        f.write(f"@echo off\n")
        f.write(f"echo Starting {main_class}...\n")
        f.write(f"{java_command}\n")
    
    print(f".bat file created: {output_bat}")


def main():
    generate_custom_jre()
    
    # 1. Get Java process startup parameters
    jcmd_output = get_java_process_info(MAIN_CLASS)
    if not jcmd_output:
        print("Failed to retrieve Java process information.")
        return

    # 2. Extract classpath
    classpath_list = parse_classpath(jcmd_output)
    if not classpath_list:
        print("No classpath found.")
        return

    # 3. Copy dependency files from classpath
    copy_dependencies(classpath_list, DEPENDENCY_DIR)

    # 4. Extract JVM arguments
    jvm_args = parse_jvm_args(jcmd_output)
    if jvm_args:
        print(f"Extracted JVM arguments: {jvm_args}")
    else:
        print("No JVM arguments found, will use defaults.")

    # 5. Extract program arguments
    java_command_pattern = re.compile(r"java_command: (.+)")
    match = java_command_pattern.search(jcmd_output)
    if match:
        java_command = match.group(1)
        args = java_command.split()[1:]
    else:
        args = []

    # 6. Copy additional files and directories
    copy_extra_files(EXTRA_FILES_AND_DIRS, PACK_DIR)

    # 7. Create .bat file with extracted JVM and program arguments
    create_bat_file(MAIN_CLASS, classpath_list, DEPENDENCY_DIR, jvm_args, args)


if __name__ == "__main__":
    main()
