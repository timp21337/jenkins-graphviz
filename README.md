Jenkins-Graphviz
================

Requirements
------------

 * Python 2.7
 * [lxml](http://lxml.de/)
 * GraphVIS

Usage example
-------------

        python jenkins_graphviz.py -v 'Some View' http://jenkins.example.com/ \
          --username <username> --password <password>
          | dot -Tsvg > some_view.svg

![Output](http://timp21337.github.io/jenkins-graphviz/some_view.svg)
