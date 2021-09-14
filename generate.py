#!/usr/bin/env python3

"""
Take semi-structured yaml data and generate README
"""


from pathlib import Path
from urllib.parse import urlparse

import yaml
from tomark import Tomark

readme = []
data = []

# Append Header
with open("_templates/header.md") as f:
    readme += f.readlines()

# Process Data
for datafile in sorted(Path("_data").glob("*.yml")):

    def valid(s):
        return True if s in info.keys() and info[s] is not None else False

    with open(str(datafile)) as f:
        info = yaml.load(f, Loader=yaml.SafeLoader)
        year = {
            "year": datafile.stem,
            "website": "",
            "wayback": "",
            "pyvideo": "",
            "repo": "",
        }

        if valid("website"):
            nicewebsite = urlparse(info["website"]).hostname
            year["website"] = f"[{nicewebsite}]({info['website']})"

        if valid("wayback"):
            year["wayback"] = f"[Wayback]({info['wayback']})"

        if "repo" in info.keys() and info["repo"] is not None:
            year["repo"] = "[Repo]({info['repo']})"

        if valid("pyvideo"):
            year["pyvideo"] = "[PyVideo]({info['pyvideo']})"

        if valid("youtube") and type(info["youtube"]) == list:
            counter = 1
            year["playlists"] = []
            for item in info["youtube"]:
                if item is not None:
                    year["playlists"].append(f"[{counter}]({item})")
                    counter += 1
            year["playlists"] = ", ".join(year["playlists"])

        data.append(year)

readme.append(Tomark.table(data))

# Append Footer
with open("_templates/footer.md") as f:
    readme += f.readlines()

# Write to Disk
with open("README.md", "w") as f:
    f.write("\n".join(readme))
