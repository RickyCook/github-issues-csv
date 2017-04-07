#!/usr/bin/env python
""" Export GitHub issues as CSV """


import csv
import sys

import click
import progressbar

from github import Github


EXCLUDE_FIELDS = (
    'id',
)


def exclude_field(name):
    return name.endswith('_url')


def get_csv_writer(issue):
    fieldnames = sorted([
        name for name in issue.raw_data.keys()
        if name not in EXCLUDE_FIELDS and not exclude_field(name)
    ])
    return csv.DictWriter(
        sys.stdout,
        fieldnames=fieldnames,
        extrasaction='ignore',
    )


@click.command(help='Export GitHub issues for a repo to CSV')
@click.option('--user', '-u', prompt='GitHub username', help='GitHub username')
@click.option('--password', '-p', prompt='GitHub password', help='GitHub password')
@click.option('--repo', '-r', prompt='GitHub repository', help='GitHub repository')
@click.option('--quick/--no-quick',
              help="Quick mode uses only data gathered from issue list",
              default=True)
def main(user, password, repo, quick):
    if user == '':
        print('No user given', file=sys.stderr)
        sys.exit(1)
    if password == '':
        print('No password given', file=sys.stderr)
        sys.exit(1)
    if repo == '':
        print('No repository given', file=sys.stderr)
        sys.exit(1)
    if '/' not in repo:
        print('Repository must be of the format "<org>/<project>"', file=sys.stderr)
        sys.exit(1)

    print('Starting in %s mode' % ('quick' if quick else 'full'), file=sys.stderr)

    api = Github(user, password)
    repo = api.get_repo(repo)
    issues = repo.get_issues(state='all')

    bar = progressbar.ProgressBar(max_value=issues.totalCount)

    csv_writer = None
    for idx, issue in bar(enumerate(issues)):
        if not csv_writer:
            csv_writer = get_csv_writer(issue)
            csv_writer.writeheader()

        data = (issue._rawData if quick else issue.raw_data).copy()
        data['labels'] = ';'.join([
            raw_label['name']
            for raw_label in (data.pop('labels', []) or [])
        ])
        data['assignees'] = ';'.join([
            raw_label['login']
            for raw_label in (data.pop('assignees', []) or [])
        ])
        data['milestone'] = (data.pop('milestone', {}) or {}).get('title', None)
        data['closed_by'] = (data.pop('closed_by', {}) or {}).get('login', None)
        data['user'] = (data.pop('user', {}) or {}).get('login', None)
        data['assignee'] = (data.pop('assignee', {}) or {}).get('login', None)
        csv_writer.writerow(data)
        sys.stdout.flush()


if __name__ == '__main__':
    main()
