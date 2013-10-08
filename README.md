Jenkins-Graphviz
================

Requirements
------------

 * Python 2.6
 * [lxml](http://lxml.de/)
 *

Usage example
-------------

        python jenkins_graphviz.py -v 'Some View' http://jenkins.example.com/ \
          --username <username> --password <password>
          | dot -Tsvg > some_view.svg


![Output](http://timp21337.github.io/jenkins-graphviz/some_view.svg)

TO print out all but a few excluded projects:

      python jenkins_views.py http://hades:8081 | \
      while read p;
      do
         python jenkins_graphviz.py http://hades:8081  -v "$p" |dot -Tsvg > "${p}.svg";
      done

If no argument is specified then the *All* view is assumed.