#!/usr/bin/env python3

"""
Take semi-structured yaml data and generate README
"""
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import subprocess

import requests
import yaml
from tomark import Tomark

script_start = datetime.now()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)
SCREENSHOTS = os.environ.get("GENERATE_SCREENSHOTS", None)

readme = []
screenshots = ""
data = []


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

    def imagetag(filename, alt):
        return f"<img src='{filename}' alt='{alt}' width='400' />"


    def capture_screenshot(url, filename, folder="screenshots"):
        if SCREENSHOTS:
            subprocess.run(
                f"pageres {url} 800x600 --overwrite --crop --filename='{filename}'",
                cwd=folder,
                shell=True,
                capture_output=True,
            )
        return imagetag(f"{folder}/{filename}.png", alt=url)

    with open(str(datafile)) as f:
        info = yaml.load(f, Loader=yaml.SafeLoader)
    
    yearnum = datafile.stem
    year = {
        "year": yearnum,
        "url": "",
        "status": "",
        "pyvideo": "❓",
        "repo": "❓",
        "youtube": "❓"
    }
    screenshots += f"### {yearnum}\n"

    if valid("canonical_url"):
        url = info["canonical_url"]
        year["status"] = str(get_status_code(url))
        year["url"] = f"[{url}]({url})"

    if valid("wayback"):
        year["status"] += f" ([Wayback]({info['wayback']}))"

        screenshots += capture_screenshot(info['wayback'], f"{yearnum}_wayback")

    if "repo" in info.keys() and info["repo"] is not None:
        repo = info["repo"]
        year["repo"] = f"[{repo}](https://github.com/{repo})"
        response = get_url(f"https://api.github.com/repos/{repo}", json=True)
        if "homepage" in response.keys():
            homepage = response["homepage"]
            year["repo"] += f" ([url]({homepage}))"
            if "glasnt" in homepage:
                year["repo"] += " 🚧"
            if urlparse(homepage).hostname == info["canonical_url"]:
                year["status"] += " ✅"
                screenshots += "None required."
            else: 
                screenshots += capture_screenshot(homepage, f"{yearnum}_repo")
    else:
        screenshots += imagetag("screenshots/placeholder.png", alt="No image")

    if valid("pyvideo"):
        pyvideo = info["pyvideo"]
        response = get_url(pyvideo)
        talk_count = response.text.count('class="entry-title"')
        year["pyvideo"] = f"[{talk_count} entries]({info['pyvideo']})"

    if valid("youtube") and type(info["youtube"]) == list:
        counter = 1
        year["youtube"] = []
        for item in info["youtube"]:
            if item is not None:
                year["youtube"].append(f"[{counter}]({item})")
                counter += 1
        year["youtube"] = ", ".join(year["youtube"])

    data.append(year)
    screenshots += f"\n\n"


readme.append(Tomark.table(data))

# Append screenshots
readme.append("## Screenshots")
readme.append("Screenshots are in the form: WayBack Machine screenshot, GitHub Pages screenshot.")
readme.append(screenshots)

# Append Footer
with open("_templates/footer.md") as f:
    readme += f.readlines()

# Write to Disk
with open("README.md", "w") as f:
    f.write("\n".join(readme))

print(f"Generated README.md in {datetime.now() - script_start}")
