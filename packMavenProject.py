import os
import xml.etree.ElementTree as ET
import subprocess
import shutil

# Configuration variables
PROJECT_DIR = r"d:\codes\myProject"  # Root directory of the Maven project
OUTPUT_DIR = r"D:\tmp\pack"  # Output directory for generated files
MAIN_CLASS = "base.SimpleStarter"  # Main class of the project
NEW_POM_FILE = os.path.join(PROJECT_DIR, "pom_executable.xml")  # Path for the newly generated POM file
JDK_PATH = r"d:\software\dev\jdk22"  # Path to JDK 22

# Read and parse the existing POM file
def read_existing_pom():
    pom_path = os.path.join(PROJECT_DIR, "pom.xml")
    if not os.path.exists(pom_path):
        print(f"Error: pom.xml not found at {pom_path}")
        exit(1)
    tree = ET.parse(pom_path)
    root = tree.getroot()
    return root, tree

# 生成一个新的POM文件，加入打包插件配置
def generate_new_pom(root, tree):
    namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}
    ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")

    # Find the <build> node, create it if not exists
    build_node = root.find("mvn:build", namespace)
    if build_node is None:
        build_node = ET.SubElement(root, "build")
    
    # Find or create the <plugins> node
    plugins_node = build_node.find("mvn:plugins", namespace)
    if plugins_node is None:
        plugins_node = ET.SubElement(build_node, "plugins")

    # Add the shade plugin if not present
    maven_shade_plugin = None
    for plugin in plugins_node.findall("mvn:plugin", namespace):
        artifact_id = plugin.find("mvn:artifactId", namespace)
        if artifact_id is not None and artifact_id.text == "maven-shade-plugin":
            maven_shade_plugin = plugin
            break

    if maven_shade_plugin is None:
        maven_shade_plugin = ET.SubElement(plugins_node, "plugin")
        group_id = ET.SubElement(maven_shade_plugin, "groupId")
        group_id.text = "org.apache.maven.plugins"
        artifact_id = ET.SubElement(maven_shade_plugin, "artifactId")
        artifact_id.text = "maven-shade-plugin"
        version = ET.SubElement(maven_shade_plugin, "version")
        version.text = "3.2.4"

        # Configure the shade plugin
        configuration_node = ET.SubElement(maven_shade_plugin, "configuration")
        
        transformers_node = ET.SubElement(configuration_node, "transformers")
        transformer_node = ET.SubElement(transformers_node, "transformer", implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer")
        
        manifest_entries_node = ET.SubElement(transformer_node, "manifestEntries")
        main_class_node = ET.SubElement(manifest_entries_node, "Main-Class")
        main_class_node.text = MAIN_CLASS
        
        multi_release_node = ET.SubElement(manifest_entries_node, "Multi-Release")
        multi_release_node.text = "true"

        filters_node = ET.SubElement(configuration_node, "filters")
        filter_node = ET.SubElement(filters_node, "filter")
        artifact_node = ET.SubElement(filter_node, "artifact")
        artifact_node.text = "*:*"
        
        excludes_node = ET.SubElement(filter_node, "excludes")
        ET.SubElement(excludes_node, "exclude").text = "META-INF/*.SF"
        ET.SubElement(excludes_node, "exclude").text = "META-INF/*.DSA"
        ET.SubElement(excludes_node, "exclude").text = "META-INF/*.RSA"

        # Add execution goals
        executions_node = ET.SubElement(maven_shade_plugin, "executions")
        execution_node = ET.SubElement(executions_node, "execution")
        id_node = ET.SubElement(execution_node, "id")
        id_node.text = "shade"
        phase_node = ET.SubElement(execution_node, "phase")
        phase_node.text = "package"
        goals_node = ET.SubElement(execution_node, "goals")
        goal_node = ET.SubElement(goals_node, "goal")
        goal_node.text = "shade"

    # Write the new POM file
    tree.write(NEW_POM_FILE, xml_declaration=True, encoding="utf-8")
    print(f"New POM file generated at: {NEW_POM_FILE}")

# Run Maven package using the new POM file
def run_maven_package():
    try:
        maven_executable = r"mvn.cmd"
        print(f"Running Maven package using new POM file: {NEW_POM_FILE}")
        subprocess.check_call([maven_executable, "-f", NEW_POM_FILE, "package", "-DskipTests"], cwd=PROJECT_DIR)
        print("Maven package completed successfully.")
    except subprocess.CalledProcessError:
        print("Error occurred during Maven packaging.")
        exit(1)

# Generate a custom JRE using jlink
def generate_custom_jre():
    try:
        jlink_executable = os.path.join(JDK_PATH, "bin", "jlink.exe")
        output_jre_dir = os.path.join(OUTPUT_DIR, "custom-jre")
        
        # Ensure the output directory does not exist; delete it if it does
        if os.path.exists(output_jre_dir):
            print(f"Directory already exists, removing: {output_jre_dir}")
            shutil.rmtree(output_jre_dir)

        # Use java --list-modules to get all available modules
        java_executable = os.path.join(JDK_PATH, "bin", "java.exe")
        available_modules = subprocess.check_output([java_executable, "--list-modules"]).decode().strip().splitlines()

        # Extract module names (only the part before @, remove version numbers)
        modules_to_add = ",".join([line.split('@')[0] for line in available_modules])

        # Generate JRE using jlink
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

# Create executable script
def create_executable_script():
    jar_file_src_path = os.path.join(PROJECT_DIR, "target", "tcs.cnnckp.base.starter-1.0.0-SNAPSHOT.jar")
    jar_file_dst_path = os.path.join(OUTPUT_DIR, "tcs.cnnckp.base.starter-1.0.0-SNAPSHOT.jar")
    script_path = os.path.join(OUTPUT_DIR, "run.bat")

    program_args = "tcs-config\\tcs-room1.conf tcs-config\\tcs-global.conf mockUcs"

    # Copy JAR file to OUTPUT_DIR
    if os.path.exists(jar_file_src_path):
        shutil.copy(jar_file_src_path, jar_file_dst_path)
        print(f"Copied JAR file to: {jar_file_dst_path}")
    else:
        print(f"Error: JAR file not found at {jar_file_src_path}")
        exit(1)

    # Generate batch script content
    script_content = f"""@echo off
set JRE_PATH=custom-jre
set MAIN_CLASS={MAIN_CLASS}
set CLASSPATH={jar_file_dst_path}
%JRE_PATH%\\bin\\java.exe --add-opens java.desktop/java.beans=ALL-UNNAMED -cp %CLASSPATH% %MAIN_CLASS% {program_args}
"""
    with open(script_path, "w") as script_file:
        script_file.write(script_content)

    print(f"Executable script created at: {script_path}")



# Main process
if __name__ == "__main__":
    root, tree = read_existing_pom()
    generate_new_pom(root, tree)

    # 运行maven package
    run_maven_package()

    # Generate a custom JRE using jlink
    generate_custom_jre()

    create_executable_script()