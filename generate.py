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


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

UNDER_CONSTRUCTION = "🚧"
OKAY = "✅"
INFO_MISSING = "❓"
SCREENSHOT_MISSING = "screenshots/placeholder.png"

readme = []
screenshots = ""
data = []


def valid(s, d={}):
    return True if s in d.keys() and d[s] is not None and d[s] != "None" else False


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

    if response.status_code == 200: 
        return "✅"
    return response.status_code


def get_url(uri, json=False):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(uri, headers=headers, timeout=5)
    return response.json() if json else response


def imagetag(filename, alt):
    return f"<img src='{filename}' alt='{alt}' width='400' />"


def capture_screenshot(url, filename, folder="screenshots"):
    subprocess.run(
        f"pageres {url} 800x600 --overwrite --crop --filename='{filename}'",
        cwd=folder,
        shell=True,
        capture_output=True,
    )
    return f"{folder}/{filename}.png"


def refresh_data():

    # Process Data
    for datafile in sorted(Path("_data").glob("*.yml")):

        with open(str(datafile)) as f:
            info = yaml.load(f, Loader=yaml.SafeLoader)

        year = datafile.stem
        info["yearnum"] = year

        if valid("canonical_url", d=info):
            url = info["canonical_url"]
            info["canonical_url_status"] = str(get_status_code(url))

        if valid("wayback", d=info):
            info["wayback_screenshot"] = capture_screenshot(
                info["wayback"], f"{year}_wayback"
            )
        else:
            info["wayback_screenshot"] = SCREENSHOT_MISSING

        info["repo_homepage_status"] = INFO_MISSING
        info["repo_homepage_screenshot"] = SCREENSHOT_MISSING
        if "repo" in info.keys() and info["repo"] is not None:
            repo = info["repo"]
            response = get_url(f"https://api.github.com/repos/{repo}", json=True)
            print(response.get("homepage", "error"))
            if "homepage" in response.keys():
                homepage = response["homepage"]
                info["repo_homepage"] = homepage
                if "glasnt" in homepage:
                    info["repo_homepage_status"] = UNDER_CONSTRUCTION
                if urlparse(homepage).hostname == info["canonical_url"]:
                    info["repo_homepage_status"] = OKAY
                info["repo_homepage_screenshot"] = capture_screenshot(
                    homepage, f"{year}_repo"
                )

        if valid("pyvideo", d=info):
            pyvideo = info["pyvideo"]
            response = get_url(pyvideo)
            talk_count = response.text.count('class="entry-title"')
            info["pyvideo_count"] = talk_count

        if valid("youtube", d=info) and type(info["youtube"]) == list:
            # todo get playlist counts
            pass

        with open(str(datafile), "w") as f:
            yaml.dump(info, f)


def generate_readme():
    readme = []
    # Append Header
    with open("_templates/header.md") as f:
        readme += f.readlines()

    data = []
    notes = []
    for datafile in sorted(Path("_data").glob("*.yml")):
        with open(str(datafile)) as f:
            info = yaml.load(f, Loader=yaml.SafeLoader)
            year = {
                "year": info["yearnum"],
                "url": f"[{info['canonical_url']}](https://{info['canonical_url']})",
                "status": info["canonical_url_status"],
                "wayback": f"[wayback]({info['wayback']})",
            }
            if valid("repo", d=info):
                year[
                    "repo"
                ] = f"[{info['repo']}](https://github.com/{info['repo']}) {info['repo_homepage_status']} "
            else:
                year["repo"] = INFO_MISSING

            
            if "youtube" in info.keys() and info["youtube"] == "None":
                year["youtube"] = "N/A"
            elif valid("youtube", d=info):
                counter = 1
                year["youtube"] = []
                for item in info["youtube"]:
                    if item is not None:
                        year["youtube"].append(f"[{counter}]({item})")
                        counter += 1
                year["youtube"] = ", ".join(year["youtube"])
            else:
                year["youtube"] = INFO_MISSING

            if "pyvideo" in info.keys() and info['pyvideo'] == "None":
                year["pyvideo"] = "N/A"
            elif valid("pyvideo", d=info) and valid("pyvideo_count", d=info):
                year["pyvideo"] = f"[{info['pyvideo_count']} entries]({info['pyvideo']})"
            else:
                year["pyvideo"] = INFO_MISSING


            if valid("notes", d=info):
               notes.append(f"* {info['yearnum']}")
               notes += [f"  * {note}" for note in info['notes'].split("\n") if note.strip() != ""]

            data.append(year)

    readme.append(Tomark.table(data))

    # Append notes (if applicable)
    if notes:
        readme.append("\n### Notes\n")
        readme.append("\n".join(notes))
        readme.append("\n")

    # Append screenshots
    readme.append("## Screenshots")
    readme.append(
        "Screenshots are in the form: WayBack Machine screenshot, GitHub Pages screenshot."
    )
    
    for datafile in sorted(Path("_data").glob("*.yml")):
        screenshots = ""
        with open(str(datafile)) as f:
            year = yaml.load(f, Loader=yaml.SafeLoader)
            readme.append(f"\n### {year['yearnum']}")
            if year["wayback"]:
                screenshots += imagetag(year["wayback_screenshot"], alt=year["wayback"])

            screenshots+= imagetag(year["repo_homepage_screenshot"], alt=year.get("repo", INFO_MISSING))
        readme.append(screenshots)

    # Append Footer
    with open("_templates/footer.md") as f:
        readme += f.readlines()

    # Write to Disk
    with open("README.md", "w") as f:
        f.write("\n".join(readme))


import click


@click.command()
@click.option(
    "--refresh",
    type=bool,
    count=True,
    default=False,
    help="regenerate dynamic data",
)
def cli(refresh):
    if refresh:
        refresh_data()
    generate_readme()


if __name__ == "__main__":
    cli()
