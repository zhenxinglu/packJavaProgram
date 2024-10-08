There are 2 ways to pack a Java program.

**packMavenProject.py** 

This script parse the pom.xml file and create a new POM file with added assembly plugin configuration.
Then it build the project with this new POM file.


**packRunningJava.py**

This script analyzes a running java process with the jcmd command, and copies the dependencies of the process
to a new folder.
