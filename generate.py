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
SCREENSHOTS = os.environ.get("GENERATE_SCREENSHOTS", None)

UNDER_CONSTRUCTION = "🚧"
OKAY = "✅"
INFO_MISSING = "❓"
SCREENSHOT_MISSING = "screenshots/placeholder.png"

readme = []
screenshots = ""
data = []


def valid(s, d={}):
    return True if s in d.keys() and d[s] is not None else False


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


def capture_screenshot(url, filename, folder="screenshots", refresh=False):
    if refresh:
        subprocess.run(
            f"pageres {url} 800x600 --overwrite --crop --filename='{filename}'",
            cwd=folder,
            shell=True,
            capture_output=True,
        )
    return f"{folder}/{filename}.png"


def refresh(refresh_screenshots=False):

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
                info["wayback"], f"{year}_wayback", refresh=refresh_screenshots
            )
        else:
            info["wayback_screenshot"] = SCREENSHOT_MISSING

        info["repo_homepage_status"] = INFO_MISSING
        info["repo_homepage_screenshot"] = SCREENSHOT_MISSING
        if "repo" in info.keys() and info["repo"] is not None:
            repo = info["repo"]
            response = get_url(f"https://api.github.com/repos/{repo}", json=True)
            if "homepage" in response.keys():
                homepage = response["homepage"]
                info["repo_homepage"] = homepage
                if "glasnt" in homepage:
                    info["repo_homepage_status"] = UNDER_CONSTRUCTION
                if urlparse(homepage).hostname == info["canonical_url"]:
                    info["repo_homepage_status"] = OKAY
                info["repo_homepage_screenshot"] = capture_screenshot(
                    homepage, f"{year}_repo", refresh=refresh_screenshots
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
    for datafile in sorted(Path("_data").glob("*.yml")):
        with open(str(datafile)) as f:
            info = yaml.load(f, Loader=yaml.SafeLoader)
            year = {
                "year": info["yearnum"],
                "url": info["canonical_url"],
                "status": info["canonical_url_status"],
                "wayback": f"[wayback]({info['wayback']})",
            }
            if valid("repo", d=info):
                year[
                    "repo"
                ] = f"[{info['repo']}](https://github.com/{info['repo']}) ([url]({info['repo_homepage']})) {info['repo_homepage_status']} "
            else:
                year["repo"] = INFO_MISSING

            if valid("youtube", d=info):
                counter = 1
                year["youtube"] = []
                for item in info["youtube"]:
                    if item is not None:
                        year["youtube"].append(f"[{counter}]({item})")
                        counter += 1
                year["youtube"] = ", ".join(year["youtube"])
            else:
                year["youtube"] = INFO_MISSING

            if valid("pyvideo", d=info):
                year["pyvideo"] = f"[{info['pyvideo_count']} entries]({info['pyvideo']})"
            else:
                year["pyvideo"] = INFO_MISSING

            data.append(year)

    readme.append(Tomark.table(data))

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
    "--refresh-data",
    type=bool,
    count=True,
    default=False,
    help="regenerate dynamic data",
)
@click.option(
    "--refresh-screenshots",
    type=bool,
    count=True,
    default=False,
    help="regenerate dynamic data",
)
def cli(refresh_data, refresh_screenshots):
    script_start = datetime.now()
    if refresh_data:
        refresh(refresh_screenshots)
    generate_readme()
    print(f"Generated README.md in {datetime.now() - script_start}")


if __name__ == "__main__":
    cli()
