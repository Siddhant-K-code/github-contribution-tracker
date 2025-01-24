import os
from datetime import datetime
import requests
import argparse

# Load GitHub Token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN environment variable not set.")

# GitHub GraphQL API endpoint
GITHUB_API_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v4.idl"
}

def get_organization_id(organization_name):
    query = """
    query($organization: String!) {
      organization(login: $organization) {
        id
      }
    }
    """
    variables = {"organization": organization_name}
    response = requests.post(GITHUB_API_URL, json={"query": query, "variables": variables}, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    if "data" in data and "organization" in data["data"] and data["data"]["organization"]:
        return data["data"]["organization"]["id"]
    else:
        raise ValueError(f"Organization '{organization_name}' not found.")

def fetch_contributions(username, organization_name):
    organization_id = get_organization_id(organization_name)
    all_contributions = {
        "data": {
            "user": {
                "contributionsCollection": {
                    "pullRequestContributions": {"nodes": []},
                    "issueContributions": {"nodes": []},
                    "commitContributionsByRepository": []
                }
            }
        }
    }

    # Query with pagination support and additional PR states
    query = """
    query($username: String!, $organizationID: ID!, $prCursor: String) {
      user(login: $username) {
        contributionsCollection(organizationID: $organizationID) {
          totalPullRequestContributions
          pullRequestContributions(first: 100, after: $prCursor, orderBy: {direction: DESC}) {
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
            nodes {
              pullRequest {
                title
                url
                state
                repository {
                  name
                }
                createdAt
                merged
                closed
              }
            }
          }
          issueContributions(first: 100) {
            nodes {
              issue {
                title
                url
                state
                repository {
                  name
                }
                createdAt
              }
            }
          }
          commitContributionsByRepository {
            repository {
              name
            }
            contributions(first: 100) {
              nodes {
                commitCount
                occurredAt
                resourcePath
                url
              }
            }
          }
        }
      }
    }
    """

    pr_cursor = None
    has_more_prs = True
    total_prs_fetched = 0

    while has_more_prs:
        variables = {
            "username": username,
            "organizationID": organization_id,
            "prCursor": pr_cursor
        }

        response = requests.post(GITHUB_API_URL, json={"query": query, "variables": variables}, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise ValueError(f"GitHub API Error: {data['errors']}")

        current_data = data["data"]["user"]["contributionsCollection"]

        # Print total expected PRs
        if total_prs_fetched == 0:
            print(f"Expected total PRs: {current_data['totalPullRequestContributions']}")

        # Process and count PRs
        pr_data = current_data["pullRequestContributions"]
        current_batch = pr_data["nodes"]
        all_contributions["data"]["user"]["contributionsCollection"]["pullRequestContributions"]["nodes"].extend(current_batch)
        total_prs_fetched += len(current_batch)
        print(f"Fetched {total_prs_fetched} PRs so far...")

        has_more_prs = pr_data["pageInfo"]["hasNextPage"]
        pr_cursor = pr_data["pageInfo"]["endCursor"] if has_more_prs else None

        # Store other contribution data only once
        if not all_contributions["data"]["user"]["contributionsCollection"]["issueContributions"]["nodes"]:
            all_contributions["data"]["user"]["contributionsCollection"]["issueContributions"]["nodes"] = current_data["issueContributions"]["nodes"]

        if not all_contributions["data"]["user"]["contributionsCollection"]["commitContributionsByRepository"]:
            all_contributions["data"]["user"]["contributionsCollection"]["commitContributionsByRepository"] = current_data["commitContributionsByRepository"]

    print(f"Total PRs fetched: {total_prs_fetched}")
    return all_contributions

def process_contributions(data):
    contributions = []
    collection = data["data"]["user"]["contributionsCollection"]

    # Process Pull Requests
    for pr in collection["pullRequestContributions"]["nodes"]:
        contributions.append({
            "type": "Pull Request",
            "title": pr["pullRequest"]["title"],
            "repository": pr["pullRequest"]["repository"]["name"],
            "status": pr["pullRequest"]["state"],
            "url": pr["pullRequest"]["url"],
            "date": datetime.strptime(pr["pullRequest"]["createdAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
        })

    # Process Issues
    for issue in collection["issueContributions"]["nodes"]:
        contributions.append({
            "type": "Issue",
            "title": issue["issue"]["title"],
            "repository": issue["issue"]["repository"]["name"],
            "status": issue["issue"]["state"],
            "url": issue["issue"]["url"],
            "date": datetime.strptime(issue["issue"]["createdAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
        })

    # Process Commits
    for repo in collection["commitContributionsByRepository"]:
        for commit in repo["contributions"]["nodes"]:
            contributions.append({
                "type": "Commit",
                "title": f"{commit['commitCount']} commits to {repo['repository']['name']}",
                "repository": repo["repository"]["name"],
                "status": "Committed",
                "url": commit["url"],
                "date": datetime.strptime(commit["occurredAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
            })

    return sorted(contributions, key=lambda x: x["date"], reverse=True)

def export_to_markdown(contributions, username, organization, filename="contributions.md"):
    with open(filename, mode="w", encoding="utf-8") as file:
        file.write(f"# GitHub Contributions for {username} in {organization}\n\n")

        # Write summary
        file.write("## Summary\n")
        pr_count = len([c for c in contributions if c["type"] == "Pull Request"])
        issue_count = len([c for c in contributions if c["type"] == "Issue"])
        commit_count = len([c for c in contributions if c["type"] == "Commit"])

        file.write(f"- Total Pull Requests: {pr_count}\n")
        file.write(f"- Total Issues: {issue_count}\n")
        file.write(f"- Total Commits: {commit_count}\n\n")

        # Write detailed contributions
        file.write("## Detailed Contributions\n\n")

        # Pull Requests section
        prs = [c for c in contributions if c["type"] == "Pull Request"]
        if prs:
            file.write("### Pull Requests\n\n")
            for pr in prs:
                file.write(f"- [{pr['title']}]({pr['url']}) - {pr['status']} ({pr['date']})\n")
            file.write("\n")

        # Issues section
        issues = [c for c in contributions if c["type"] == "Issue"]
        if issues:
            file.write("### Issues\n\n")
            for issue in issues:
                file.write(f"- [{issue['title']}]({issue['url']}) - {issue['status']} ({issue['date']})\n")
            file.write("\n")

        # Commits section
        commits = [c for c in contributions if c["type"] == "Commit"]
        if commits:
            file.write("### Commits\n\n")
            for commit in commits:
                file.write(f"- [{commit['title']}]({commit['url']}) - {commit['date']}\n")
            file.write("\n")

    return filename

def main():
    parser = argparse.ArgumentParser(description="GitHub Contribution Tracker")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("organization", help="GitHub organization name")
    args = parser.parse_args()

    try:
        print(f"Fetching contributions for {args.username} in {args.organization}...")
        raw_data = fetch_contributions(args.username, args.organization)
        contributions = process_contributions(raw_data)
        output_file = export_to_markdown(contributions, args.username, args.organization)
        print(f"Successfully exported contributions to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
