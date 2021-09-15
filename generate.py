#!/usr/bin/env python3

"""
Take semi-structured yaml data and generate README
"""
import os
import requests
from pathlib import Path
from urllib.parse import urlparse

import yaml
from tomark import Tomark

readme = []
data = []

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

# Append Header
with open("_templates/header.md") as f:
    readme += f.readlines()

# Process Data
for datafile in sorted(Path("_data").glob("*.yml")):

    def valid(s):
        return True if s in info.keys() and info[s] is not None else False
    
    def get_status_code(uri):
        try:
            response = get_url(f"https://{uri}")
        except requests.exceptions.ConnectTimeout: 
            return "Timeout"
        except requests.exceptions.SSLError:
            try: 
                response = get_url(f"http://{uri}")
                if "default web page for this server" in response.text:
                    return "Invalid config"
            except requests.exceptions.SSLError:
                return "SSL Error"
         
        return response.status_code 

    def get_url(uri, json=False):
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(uri, headers=headers, timeout=5)
        return response.json() if json else response

    with open(str(datafile)) as f:
        info = yaml.load(f, Loader=yaml.SafeLoader)
        year = {
            "year": datafile.stem,
            "url": "",
            "status": "",
            "wayback": "",
            "pyvideo": "",
            "repo": "",
            "repo_url": "",
        }

        if valid("canonical_url"):
            url = info["canonical_url"]
            year["status"] = get_status_code(url)
            year["url"] = f"[{url}]({url})"

        if valid("wayback"):
            year["wayback"] = f"[Wayback]({info['wayback']})"

        if "repo" in info.keys() and info["repo"] is not None:
            repo = info['repo']
            year["repo"] = f"[Repo]({repo})"
            response = get_url(f"https://api.github.com/repos/{repo}", json=True)
            if "homepage" in response.keys():
                year["repo_url"] = response["homepage"]


        if valid("pyvideo"):
            pyvideo = info["pyvideo"]
            response = get_url(pyvideo)
            talk_count = response.text.count('class="entry-title"')
            year["pyvideo"] = f"[PyVideo]({info['pyvideo']}) ({talk_count} entries)"

        if valid("youtube") and type(info["youtube"]) == list:
            counter = 1
            year["youtube"] = []
            for item in info["youtube"]:
                if item is not None:
                    year["youtube"].append(f"[{counter}]({item})")
                    counter += 1
            year["youtube"] = ", ".join(year["youtube"])

        data.append(year)

readme.append(Tomark.table(data))

# Append Footer
with open("_templates/footer.md") as f:
    readme += f.readlines()

# Write to Disk
with open("README.md", "w") as f:
    f.write("\n".join(readme))
