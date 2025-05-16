# Java Application Packaging Tools

This project provides two powerful Python scripts to simplify the packaging and distribution of Java applications. Whether you're working with Maven projects or need to capture a running Java application's dependencies, these tools streamline the process of creating standalone, executable packages.

## Why Use These Tools?

- **Simplified Deployment**: Create self-contained packages with all dependencies included
- **Custom JRE Generation**: Automatically create optimized JREs with only the required modules
- **Easy Distribution**: Ready-to-run executables that work on any compatible system
- **No Manual Configuration**: Automatic detection of dependencies and configuration

## Available Tools

### 1. **packMavenProject.py** - Maven-Based Packaging

This script automates the packaging of a Maven project by:

- Parsing an existing `pom.xml` file and generating a new POM with Maven Shade Plugin configuration
- Building an executable JAR with all dependencies included
- Generating a custom, optimized JRE using `jlink` that includes only the necessary Java modules
- Creating a Windows batch file (`run.bat`) to execute the application

#### Key Features:
- **Automated Configuration**: No need to manually configure the Maven Shade Plugin
- **Custom JRE**: Creates a smaller, optimized Java Runtime Environment
- **Simple Execution**: Single-click batch file to run the application
- **Preserve Program Arguments**: Automatically includes necessary program arguments

#### Usage:
1. Configure the project directory, output directory, and main class variables at the top of the script
2. Run: `python packMavenProject.py`
3. Find the packaged application in the specified output directory

### 2. **packRunningJava.py** - Running Process Packaging

This script takes a unique approach by analyzing a running Java process to:

- Extract the exact classpath, JVM arguments, and program arguments using `jcmd`
- Copy all dependencies to a structured output directory
- Generate a custom JRE that matches the running application's requirements
- Create a Windows batch file (`start_program.bat`) that reproduces the exact application configuration

#### Key Features:
- **Runtime Analysis**: Captures the exact runtime configuration of a working application
- **Dependency Discovery**: Automatically identifies and copies all required dependencies
- **Path Structure Preservation**: Maintains the directory structure of dependencies
- **IDE-Independent**: Removes IDE-specific arguments for clean execution
- **Extra Files Support**: Ability to include additional configuration files and directories

#### Usage:
1. Configure `JDK_PATH`, `MAIN_CLASS`, and `PACK_DIR` variables at the top of the script
2. Start the Java application you want to package
3. Run: `python packRunningJava.py`
4. Go to the specified `PACK_DIR` and run `start_program.bat` to execute the packaged application

## Which Approach Should You Choose?

| Feature | packMavenProject.py | packRunningJava.py |
|---------|---------------------|-------------------|
| Source Required | Yes (Maven project) | No (works with running binaries) |
| Captures Runtime Config | No | Yes (exact running configuration) |
| Works with Non-Maven Projects | No | Yes (any Java application) |
| Custom JRE Generation | Yes | Yes |
| Dependency Detection | From POM | From Runtime |
| Best For | New projects, Maven-based development | Existing applications, complex configurations |

## Requirements

- Python 3.6+
- JDK 22 (or compatible version)
- Maven (for packMavenProject.py)
- A running Java application (for packRunningJava.py)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
