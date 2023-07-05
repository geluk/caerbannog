# Caerbannog

Caerbannog makes it easy to write declarative Python scripts to automatically
configure your local user accounts.

## Example

### Create a configuration script

First, create a configuration script to describe the various types of devices
on which you want to configure your user account:

`./configure.py:`
```py
from caerbannog.prelude import *

target("laptop").depends_on("windows")
target("desktop").depends_on("archlinux")
target("work-laptop").depends_on("windows").has_roles("vscode")

target("windows").depends_on("common").has_roles("powershell", "windows-terminal")
target("archlinux").depends_on("common").has_roles("zsh", "bspwm", "vim")

target("common").has_roles("git")

commit()
```

### Create role files

Now create roles which describe applications or configurations that you want to
deploy. For instance, for git, you may want to install the package and create
a `.gitconfig` and global `.gitignore` in your home directory:

`roles/git/role.py:`
```py
from caerbannog.roles.prelude import *

def configure():
    Do(
        Package("git").is_installed(),
        File(home_dir(".gitconfig")).has_template("gitconfig.j2"),
        File(home_dir(".gitignore")).has_lines(".vscode"),
    )
```

`roles/git/gitconfig.j2:`
```
[core]
	hooksPath = "~/.githooks"
[user]
	name = Edsger Dijkstra
	email = dijkstra@novigrad.rd
[fetch]
	prune = true
[pull]
	rebase = true
```

### Run it!

Now run the script to bring your machine to its desired state:

```
$ python configure.py configure laptop
```

All actions that are taken and changes that are made are clearly reported:
![image](https://github.com/geluk/caerbannog/assets/1516985/d03f5428-b350-49af-829c-7a3696a43000)



## How does it work?

Caerbannog allows you to write code that specifies what your system should look
like. For instance, you can declare that the file `.gitignore` in your home
directory has `.vscode` as its content in the following manner:

```py
File(home_dir(".gitignore")).has_lines(".vscode")
```

If the file exists in your home directory, and it has the content you specified,
no action will be taken. If it is not present, it will be created. If it exists,
but its content differs, it will be modified.

To keep related assertions together, you can group them by creating roles, and
placing all related assertions within those roles. In this case, it makes sense
to create a `git` role which also asserts that your `.gitignore` has the right
content, and that the `git` package is installed.

Often, you will want to configure multiple devices, and not always all in the
same way. To allow for this, you can create targets. By assigning roles to
targets, you can selectively apply roles to different devices.

These targets are specified in the `configure.py` script.
```py
target("laptop").has_roles("git")
```

Now, if you run the script, you can apply the `git` role by selecting the
`laptop` target:

```
python ./configure.py configure laptop
```
