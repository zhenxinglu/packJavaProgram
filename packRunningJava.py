# Create a runnable TCS pacakge, jars/config file/JRE are included.
# 
# Steps to use this script.
# 1) configure these 2 variables: JDK_PATH and PACK_DIR
# 2) start TCS from Intellij IDEA
# 3) run this scrtip:  >  python packRunningJava.py
# 4) go to PACK_DIR, and double click start_program.bat


import os
import subprocess
import shutil
import re

# 配置全局变量
JDK_PATH = r"d:\software\dev\jdk22" 
MAIN_CLASS = "tcs.base.starter.SimpleStarter"
PACK_DIR = "D:\\tmp\\pack2"  # 打包后的目标目录
DEPENDENCY_DIR = os.path.join(PACK_DIR, "dependencies")  # 依赖的目录
EXTRA_FILES_AND_DIRS = [
    "D:\\codes\\cnnckp_tcs\\base\\starter\\archive",
    "D:\\codes\\cnnckp_tcs\\base\\starter\\nfsSharedStorage",
    "D:\\codes\\cnnckp_tcs\\base\\starter\\ois",
    "D:\\codes\\cnnckp_tcs\\base\\starter\\persistence",
    "D:\\codes\\cnnckp_tcs\\base\\starter\\tps_repository",
    "D:\\codes\\cnnckp_tcs\\tcs-config"
]



# 使用 jlink 生成自定义 JRE
def generate_custom_jre():
    try:
        jlink_executable = os.path.join(JDK_PATH, "bin", "jlink.exe")  # jlink 的路径
        output_jre_dir = os.path.join(PACK_DIR, "custom-jre")  # 自定义 JRE 输出目录
        
        # 确保输出目录不存在，若存在则删除
        if os.path.exists(output_jre_dir):
            print(f"Directory already exists, removing: {output_jre_dir}")
            shutil.rmtree(output_jre_dir)

        # 使用 java --list-modules 来获取所有可用模块
        java_executable = os.path.join(JDK_PATH, "bin", "java.exe")
        available_modules = subprocess.check_output([java_executable, "--list-modules"]).decode().strip().splitlines()

        # 提取模块名（只提取 @ 前面的部分，去掉版本号）
        modules_to_add = ",".join([line.split('@')[0] for line in available_modules])

        # 使用 jlink 生成 JRE
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



# 获取某个 Java 进程的信息
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


# 解析 jcmd 的输出以提取 classpath
def parse_classpath(jcmd_output):
    classpath_pattern = re.compile(r"java_class_path \(initial\): (.+)")
    match = classpath_pattern.search(jcmd_output)
    
    if match:
        classpath = match.group(1)
        return classpath.split(';')
    
    return []


# 复制 classpath 中的依赖文件
def copy_dependencies(classpath_list, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for path in classpath_list:
        if os.path.exists(path):
            try:
                # 获取驱动器部分并转换为小写
                drive, tail = os.path.splitdrive(path)
                drive_letter = drive.lower().rstrip(':')

                # 构造目标路径，保留整个路径结构，包括驱动器部分 l
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


# 复制额外的目录和文件
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


# 生成启动 Java 程序的 .bat 文件
def create_bat_file(main_class, classpath_list, target_directory):
    classpath = ";".join([
        os.path.join(target_directory, os.path.splitdrive(p)[0].lower().rstrip(':'), os.path.splitdrive(p)[1].lstrip("\\"))
        for p in classpath_list
    ])
    
    vmOptiions = "--add-opens=java.desktop/java.beans=ALL-UNNAMED"
    args = ["tcs-config/tcs-room1.conf",  "tcs-config/tcs-global.conf", "0",  "mockUcs"]
    
    java_command = f'custom-jre\\bin\\java {vmOptiions} -cp "{classpath}" {main_class} {" ".join(args)}'
    output_bat = os.path.join(PACK_DIR, "start_program.bat")

    with open(output_bat, 'w') as f:
        f.write(f"@echo off\n")
        f.write(f"echo Starting {main_class}...\n")
        f.write(f"{java_command}\n")
    
    print(f".bat file created: {output_bat}")


def main():
    generate_custom_jre()
    
    # 1. 获取 Java 进程的启动参数
    jcmd_output = get_java_process_info(MAIN_CLASS)
    if not jcmd_output:
        print("Failed to retrieve Java process information.")
        return

    # 2. 提取 classpath
    classpath_list = parse_classpath(jcmd_output)
    if not classpath_list:
        print("No classpath found.")
        return

    # 3. 复制 classpath 中的依赖文件
    copy_dependencies(classpath_list, DEPENDENCY_DIR)

    # 4. 提取其他启动参数
    java_command_pattern = re.compile(r"java_command: (.+)")
    match = java_command_pattern.search(jcmd_output)
    if match:
        java_command = match.group(1)
        args = java_command.split()[1:]
    else:
        args = []

    # 5. 复制额外的文件和目录
    copy_extra_files(EXTRA_FILES_AND_DIRS, PACK_DIR)

    # 6. 创建 .bat 文件
    create_bat_file(MAIN_CLASS, classpath_list, DEPENDENCY_DIR)


if __name__ == "__main__":
    main()
