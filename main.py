import requests
from bs4 import BeautifulSoup
from decouple import config
import json


def get_headers():
    token = config("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {token}"
    }
    return headers


def get_repos(organisation_name):
    url = f"https://api.github.com/orgs/{organisation_name}/repos"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return [repo['name'] for repo in response.json()]
    elif response.status_code == 403:
        print("Rate limit exceeded or access denied. Please check your token.")
    return []


def get_branches(organisation_name, repo_name):
    url = f"https://api.github.com/repos/{organisation_name}/{repo_name}/branches"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return [branch['name'] for branch in response.json()]
    elif response.status_code == 403:
        print("Rate limit exceeded or access denied. Please check your token.")
    return []


def get_files_and_dirs(organisation_name, repo_name, branch_name, current_path=""):
    url = f"https://github.com/{organisation_name}/{repo_name}/tree/{branch_name}/{current_path}"

    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        files_and_dirs = []

        for ccn in soup.find_all('a', {'aria-label': True, 'class': 'Link--primary'}):
            relative_path = ccn.get('href')
            full_url = f"https://github.com{relative_path}"

            if f"/tree/{branch_name}/" in relative_path:
                directory_path = relative_path.split(f"/{repo_name}/tree/{branch_name}/")[-1]
                contents = get_files_and_dirs(organisation_name, repo_name, branch_name, directory_path)

                files_and_dirs.append({
                    "name": directory_path.split('/')[-1],
                    "type": "directory",
                    "url": full_url,
                    "contents": contents
                })
            elif f"/blob/{branch_name}/" in relative_path:
                files_and_dirs.append({
                    "name": relative_path.split('/')[-1],
                    "type": "file",
                    "url": full_url
                })

        return files_and_dirs
    elif response.status_code == 403:
        print("Rate limit exceeded or access denied. Please check your token.")
    return []


def scrape_organisation_files_and_dirs(organisation_name):
    repos = get_repos(organisation_name)
    org_structure = {}
    for repo in repos:
        branches = get_branches(organisation_name, repo)
        for branch in branches:
            print(f"\nScraping repository: {repo} (Branch: {branch})")
            files_and_dirs = get_files_and_dirs(organisation_name, repo, branch)

            if repo not in org_structure:
                org_structure[repo] = {}
            org_structure[repo][branch] = files_and_dirs

    return org_structure


def save_to_json(structure_by_repo, filename='scraped_links.json'):
    with open(filename, mode='w') as file:
        json.dump(structure_by_repo, file, indent=4)
    print(f"Data saved to {filename}")


if __name__ == "__main__":
    organisation_name = config("ORG_NAME")
    structure_by_repo = scrape_organisation_files_and_dirs(organisation_name)
    save_to_json(structure_by_repo)
