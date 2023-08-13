# JoyA's F1Manager Companion

JoyA's F1Manager Companion is a small app designed to enhance the experience playing F1Manager.

The first version only includes a Database Editor: it allows you to edit eveything in the database, with a few convenience features. A lot more coming !

:warning: This is early in the project, expect bugs and a lot of memory usage

## How to use

:warning: tested on Windows 10 for F1Manager 23 only

### Requirements
- install Docker Desktop https://www.docker.com/products/docker-desktop/

### Starting the app for the first time, or after an update
- go to the Docker Desktop search bar, search `josselingirault/f1manager-companion`
- select latest version, click pull
- go to Docker Desktop > Images
- click on the image named `josselingirault/f1manager-companion`
- on the top-right, click `Run`
- unroll `Optional settings` and set the values
    - `Host port` : 8501
    - `Volumes`
        - `Host path` : select your F1Manager `SaveGames` folder, normally found at `/C/Users/<name>/AppData/Local/F1Manager23/Saved/SaveGames`
        - `Container path` : `/usr/home/project/saves`
- click `Run`
- App has started ! Go to `localhost:8501` in your favorite browser
- You can stop the App by clicking on the `Stop` button in Docker Desktop

### If you've already started this version once
- go to Docker Desktop > Containers
- select the container you want to start and click `Start`
- App has started ! Go to `localhost:8501` in your favorite browser


## FAQ

#### Why Docker ? It uses so much memory
Thanks to using Docker, no one has to worry about having the correct version of python or whatever installed. It's also a tool I use everyday at work while I've got no idea how to package a javascript app. But I agrre I also need to work on minimizing the size :)

### I've got problems with the amount of memory the app takes, for real though
Look up https://learn.microsoft.com/en-us/windows/wsl/wsl-config#configure-global-options-with-wslconfig
