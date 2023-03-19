# Documentation

This project generates the README.md from `generate.py`, which includes things like dynamically checking values and rendering the README table. 

## Generated README.md

Some data is stored in the `_data/` YAML files, but a lot is dynamically pulled, including: 

 * url status codes
 * repo settings
 * pyvideo listings

This could be stored more statically to make the generation run faster (~25s, ~3m w/screenshots). 

## Archives

Some archives are from previous scrapes, some from [`wayback_machine_downloader`](https://github.com/hartator/wayback-machine-downloader), which gets a download from WayBack machine.

You can then customise this output in a few ways. What follows is some WIP notes: 

 * use search/replace across all files
   * in VS Code with `command shift h` (or the magnifying glass icon on the left)
 * literal html may presume a subdomain, not a subfolder, so to save you re-writing many things use a custom domain on GitHub pages
 * create a `404.md` to mark that something was actually a 404


## Screenshots

There are many ways to do this, but this way is taken from the DjangoCon archive project: 

```
npm install -g pageres-cli
```

Screenshots are updated in `generate.py` if `--refresh` is a parameter.