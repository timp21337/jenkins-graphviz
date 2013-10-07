#!/usr/bin/env python

from __future__ import print_function

import argparse
import base64
import itertools
import json
import string
import urllib
import urlparse
import urllib2
import sys

import lxml.objectify

dot_template = '''
digraph {    
    graph [rankdir="LR",fontsize=16,fontname="Sans"]
    labelloc=top;
    label="Jobs on $server";


    node [fontname="Sans",fontsize=9]

// repos
$repos

// trigger edges
$trigger_edges

    subgraph cluster_view {
        label = "$view_name"
// view jobs
$view_jobs
    }

    $other_jobs
    $subproject_edges
    $pipeline_edges

}
'''


def view_url(base, view):
    '''
    >>> view_url('http://server/', '')
    'http://server/'
    >>> view_url('http://server/', 'All')
    'http://server/view/All/'
    >>> view_url('http://server/', 'With Space')
    'http://server/view/With%20Space/'
    >>> view_url('http://server', 'missing_slash')
    'http://server/view/missing_slash/'

    '''
    return urlparse.urljoin(base, 'view/{0}/'.format(urllib.quote(view)) if view else '')


def http_fetch(url, username=None, password=None):
    request = urllib2.Request(url, None)
    if username is not None:
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
    try:
        return urllib2.urlopen(request)
    except:
        print('While fetching <{0}>:'.format(url), file=sys.stderr)
        if username is not None:
            print('Using username <{0}>'.format(username), file=sys.stderr)
        raise


def api_fetch(url, username=None, password=None):
    url = urlparse.urljoin(url, 'api/json')
    return json.load(http_fetch(url, username, password))


def fix_job(job):
    if job['color'] == 'disabled':
        job['color'] = 'grey'
    if job['color'] == 'blue_anime':
        job['color'] = 'blue'
    return job


def get_views():
    return ['Test']


def output_to_dot_file(server, username, password, view):
    view_jobs = {}
    other_jobs = {}
    pipeline_edges = set()
    subproject_edges = set()
    repos = set()
    trigger_edges = set()

    url = view_url(server, view)

    for job in api_fetch(url, username, password)['jobs']:
        view_jobs[job['name']] = fix_job(job)

    # Downstreams are when a job uses the 'build other projects' post-build action
    for job in view_jobs.values():
        job_detail = api_fetch(job['url'], username, password)
        for downstream in job_detail['downstreamProjects']:
            pipeline_edges.add((job['name'], downstream['name']))
            if downstream['name'] not in view_jobs:
                other_jobs[downstream['name']] = fix_job(downstream)
        for upstream in job_detail['upstreamProjects']:
            pipeline_edges.add((upstream['name'], job['name']))
            if upstream['name'] not in view_jobs:
                other_jobs[upstream['name']] = fix_job(upstream)

    for job in itertools.chain(view_jobs.values(), other_jobs.values()):
        job['config'] = lxml.objectify.parse(
            http_fetch(urlparse.urljoin(job['url'], 'config.xml'), username, password))

        job['subprojects'] = set()
        subprojects = job['config'].xpath(
            '/*/builders/hudson.plugins.parameterizedtrigger.TriggerBuilder/' +
            'configs/hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig/projects')
        if subprojects:
            job['subprojects'].update([s.strip() for s in str(subprojects[0]).split(',')])

        for subproject in job['subprojects']:
            subproject_edges.add((job['name'], subproject))

        job['enabled'] = not job['config'].xpath('/*/disabled')[0]

    for job in view_jobs.values():
        for repo in job['config'].xpath('/*/scm/userRemoteConfigs/hudson.plugins.git.UserRemoteConfig'):
            for branch in job['config'].xpath('/*/scm/branches/hudson.plugins.git.BranchSpec'):
                for trigger in job['config'].xpath('/*/triggers/*'):
                    if trigger.tag in ['hudson.triggers.TimerTrigger',
                                       'hudson.triggers.SCMTrigger',
                                       'com.cloudbees.jenkins.GitHubPushTrigger']:
                        repos.add((str(repo.url).rpartition('/')[2], branch.name))
                        trigger_edges.add((((str(repo.url).rpartition('/')[2], branch.name)), job['name']))
                        break
                    print('Unknown trigger: {}', file=sys.stderr)

    print(string.Template(dot_template).substitute({
        'repos': '\n'.join(
            ['"{0}\\n{1}" [URL="{2}",shape=oval]'.format(
                repo[0], repo[1], str(repo[0]).replace('git@github.com:', '', 1)) for repo in repos]),
        'server': server,
        'view_name': view if view else '',
        'trigger_edges': '\n'.join(
            ['"{0}\\n{1}" -> "{2}"'.format(repo[0], repo[1], job) for repo, job in trigger_edges]),
        'view_jobs': '\n'.join(['"{0}" [shape="box", URL="{1}", color="{2}", fontcolor="{3}"]'.format(
            job['name'],
            job['url'],
            job['color'],
            'black' if job['enabled'] else 'grey'
        ) for name, job in sorted(view_jobs.iteritems())]),
        'other_jobs': '\n'.join(['"{0}" [shape="box", URL="{1}", color="{2}"]'.format(
            job['name'],
            job['url'],
            job['color']) for name, job in sorted(other_jobs.iteritems())]),
        'pipeline_edges': '\n'.join(['"{0}" -> "{1}"'.format(a, b) for a, b in pipeline_edges]),
        'subproject_edges': '\n'.join(['"{0}" -> "{1}" [style=dotted]'.format(a, b) for a, b in subproject_edges])
    }))


def main():
    parser = argparse.ArgumentParser(description='Output a Graphviz graph based on relationships between Jenkins jobs')
    parser.add_argument('server', help='URL of Jenkins server')
    parser.add_argument('--view', '-v', help='Filter jobs by view')
    parser.add_argument('--username', '-u', help='Jenkins username')
    parser.add_argument('--password', '-p', help='Jenkins password')

    args = parser.parse_args()

    view_name = args.view.replace('\"', '')
    if args.view is not None:
        views = [view_name]
    else:
        views = ['All']
    for view in views:
        output_to_dot_file(args.server, args.username, args.password, view)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
