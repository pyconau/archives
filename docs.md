# Documentation

This project generates the README.md from `generate.py`, which includes things like dynamically checking values and rendering the README table. 

## Archives

Some archives are from previous scrapes, some from [`wayback_machine_downloader`](https://github.com/hartator/wayback-machine-downloader), which gets a download from WayBack machine.

You can then customise this output in a few ways. What follows is some WIP notes: 

 * use search/replace across all files
   * in VS Code with `command shift h` (or the magnifying glass icon on the left)
 * literal html may presume a subdomain, not a subfolder, so to save you re-writing many things use a custom domain on GitHub pages
 * create a `404.md` to mark that something was actually a 404
