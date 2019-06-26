TENNIS RANKING
=============

## Installation

### Python

```
Windows and Mac: https://www.python.org/downloads/
Mac (with Homebrew): In the terminal, run brew install python3
Debian/Ubuntu/Mint: In the terminal, run sudo apt-get install python3

From the terminal run: python --version to check python is running
```

### Installing the Vagrant VM
Note: If you already have a vagrant machine installed skip to the 'Fetch the Source Code and VM Configuration' section

You'll use a virtual machine (VM) to run a web server and a web app that uses it. The VM is a Linux system that runs on top of your own machine. You can share files easily between your computer and the VM.

We're using the Vagrant software to configure and manage the VM. Here are the tools you'll need to install to get it running:

#### Git
If you don't already have Git installed, download Git from git-scm.com. Install the version for your operating system.

On Windows, Git will provide you with a Unix-style terminal and shell (Git Bash). (On Mac or Linux systems you can use the regular terminal program.)

You will need Git to install the configuration for the VM. 

#### VirtualBox
VirtualBox is the software that actually runs the VM. You can download it from [virtualbox.org, here](https://www.virtualbox.org/wiki/Downloads). Install the platform package for your operating system. You do not need the extension pack or the SDK. You do not need to launch VirtualBox after installing it.

Ubuntu 14.04 Note: If you are running Ubuntu 14.04, install VirtualBox using the Ubuntu Software Center, not the virtualbox.org web site. Due to a reported bug, installing VirtualBox from the site may uninstall other software you need.

#### Vagrant
Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem. You can download it from [vagrantup.com](https://www.vagrantup.com/downloads.html). Install the version for your operating system.

Windows Note: The Installer may ask you to grant network permissions to Vagrant or make a firewall exception. Be sure to allow this.


### Fetch the Source Code and VM Configuration
Windows: Use the Git Bash program (installed with Git) to get a Unix-style terminal.

Other systems: Use your favorite terminal program.

#### Copy project

Unzip the file tennis_ranking.zip to the vagrant directory 

#### Run the virtual machine
Using the terminal, type `vagrant up` to launch your virtual machine.

## Run the Tennis Ranking App
Now that you have Vagrant up and running type `vagrant ssh` to log into your VM. Change directory to the /vagrant directory by typing `cd /vagrant`. This will take you to the shared folder between your virtual machine and host machine.

Then change directory to the catalog directory by typing `cd catalog`.

Type ls to ensure that you are inside the directory that contains application.py and two directories named 'templates' and 'static'

Now type `python database_setup.py` to initialize the database.

Type `python application.py` to run the Flask web server. In your browser visit `http://localhost:8000` to view the tennis ranking app. You should be able to view, add, edit, and delete clubs and respective associates.

When you want to log out, type exit at the shell prompt. To turn the virtual machine off (without deleting anything), type vagrant halt. If you do this, you'll need to run vagrant up again before you can log into it.

### Access JSON endpoint
Visit  `http://localhost:8000/club/JSON` to get the JSON for all registered clubs.

Visit  `http://localhost:8000/club/<club_id>/associates/JSON` to get the JSON for all associates of the club registered as <club_id>.


