#! /usr/bin/python
# -*- coding: utf8 -*-

# Copyright 2009-2010 Gabriel Sean Farrell
# Copyright 2008-2010 Mark A. Matienzo
#
# This file is part of Kochief.
#
# Kochief is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kochief is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kochief.  If not, see <https://www.gnu.org/licenses/>.

"""Indexes documents in a Solr instance."""

import json
import optparse
import os
import sys
import time
import urllib
import urllib2

os.nice( 19 )

try:
    import xml.etree.ElementTree as et  # builtin as of Python 2.5
except ImportError:
    import elementtree.ElementTree as et

import django.conf as conf
import django.core.management.base as mb
# from django.utils import simplejson

CSV_FILE = 'tmp.csv'

# class Command(mb.BaseCommand):

from django.core.management.base import BaseCommand, CommandError
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
                    '--expired',
                    # action='store_true',
                    dest='expired',
                    # default=False,
                    help='Delete records older than six months.',
                )

    # option_list = mb.BaseCommand.option_list + (
    #     optparse.make_option('-c', '--collection',
    #         action='append',
    #         dest='collections',
    #         metavar='COLLECTION',
    #         help='Append COLLECTIONs to "collection" field on docs as they are indexed. More than one collection can be applied (e.g., --collection=books --collection=oversized).'),
    #     optparse.make_option('-n', '--new',
    #         action='store_true',
    #         dest='new',
    #         help='Create a new index.  If the index already exists, all docs in the index will be deleted before this indexing.'),
    #     optparse.make_option('-d', '--delete',
    #         #action='delete',
    #         dest='delete_rec',
    #         help='Delete a record by id.'),
    #     optparse.make_option('-s', '--delete_set',
    #         #action='delete',
    #         dest='delete_set',
    #         help='Delete a set given a Solr url of search results.'),
    #     optparse.make_option('-e', '--expired',
    #         #action='delete',
    #         dest='expired',
    #         help='Delete records older than six months.'),
    #     optparse.make_option('-u', '--not_updated',
    #         #action='delete',
    #         dest='not_updated',
    #         help='Deletes records that dont have a recent last update.  See settings.py for parameters.'),
    #     optparse.make_option('-o', '--optimize',
    #         #action='delete',
    #         dest='optimize',
    #         help='Optimizes the index.  See settings.py for parameters.'),
    #     optparse.make_option('-p', '--parser',
    #         dest='parser',
    #         metavar='PARSER',
    #         help='Use PARSER (in discovery/parsers) to parse files or urls for indexing'),
    # )
    help = 'Indexes documents in a Solr instance.'
    args = '[file_or_url ...]'

    # def handle(self, *file_or_urls, **options):
    def handle(self, *args, **options):
        print( 'options, ```%s```' % options )
        new = options.get('new')
        delete_rec = options.get('delete_rec')
        expired = options.get('expired')
        not_updated = options.get('not_updated')
        delete_set_url = options.get('delete_set')
        optimize = options.get('optimize')
        if delete_rec:
            data = '<delete><query>id:%s</query></delete>' % delete_rec
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to deletion request for rec with id: %s" % delete_rec
            print f.read()
        if delete_set_url:
            #Pass in result set url
            # delete_set_response = simplejson.load(urllib2.urlopen(delete_set_url.strip('"')))
            file_handler = urllib2.urlopen( delete_set_url.strip('"') )
            delete_set_response = json.loads( file_handler.read() )
            delete_set = []
            solr_data = ""
            for doc in delete_set_response['response']['docs']:
                delete_set.append(doc['id'])
                solr_data += '<query>id:%s</query>' % doc['id']
            delete_set = ",".join(delete_set)
            print "Deleting %s" % delete_set
            data = '<delete>%s</delete>' % solr_data
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to deletion request"
            print f.read()
        if new:
            data = '<delete><query>*:*</query></delete>'
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to deletion request:"
            print f.read()
        if expired:
            data = '<delete><query>%s</query></delete>' % conf.settings.EXPIRED_RECORDS_QUERY
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to deletion request for records with a cat date older than the time specified in settings.py."
            print f.read()
        if not_updated:
            data = '<delete><query>%s</query></delete>' % conf.settings.NOT_UPDATED_RECORDS_QUERY
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to deletion request for records not updated since the time specified in settings.py."
            print f.read()
        if optimize:
            print "Will optimize: %s." % conf.settings.SOLR_URL
            data = '<optimize/>'
            r = urllib2.Request(conf.settings.SOLR_URL + 'update?commit=true')
            r.add_header('Content-Type', 'text/xml')
            r.add_data(data)
            f = urllib2.urlopen(r)
            print "Solr response to optimize request."
            print f.read()
        if file_or_urls:
            parser = options.get('parser')
            module = None
            if parser:
                if parser.endswith('.py'):
                    parser = parser[:-3]
                module = __import__('kochief.discovery.parsers.' + parser, globals(),
                        locals(), [parser])
        for file_or_url in file_or_urls:
            if not module:
                # guess parser based on file extension
                if file_or_url.endswith('.mrc'):
                    import kochief.discovery.parsers.marc as module
            if not module:
                raise mb.CommandError("Please specify a parser.")
            print "Converting %s to CSV ..." % file_or_url
            t1 = time.time()
            try:
                data_handle = urllib.urlopen(file_or_url)
            #For Windows.  Urllib will fail on opening a local file.
            except IOError:
                data_handle = open(file_or_url)
            try:
                #For Windows open as binary or else blank rows will be created in the CSV.
                csv_handle = open(CSV_FILE, 'wb')
                record_count = module.write_csv(data_handle, csv_handle,
                        collections=options.get('collections'))
            finally:
                csv_handle.close()
            t2 = time.time()
            load_solr(CSV_FILE)
            t3 = time.time()
            os.remove(CSV_FILE)
            p_time = (t2 - t1) / 60
            l_time = (t3 - t2) / 60
            t_time = p_time + l_time
            rate = record_count / (t3 - t1)
            print """Processing took %0.3f minutes.
Loading took %0.3f minutes.
That's %0.3f minutes total for %d records,
at a rate of %0.3f records per second.
""" % (p_time, l_time, t_time, record_count, rate)


def get_multi():
    """Inspect solr schema.xml for multivalue fields."""
    multivalue_fieldnames = []
    schema = et.parse(conf.settings.SOLR_DIR + 'conf/schema.xml')
    fields_element = schema.find('fields')
    field_elements = fields_element.findall('field')
    for field in field_elements:
        if field.get('multiValued') == 'true':
            multivalue_fieldnames.append(field.get('name'))
    return multivalue_fieldnames

def load_solr(csv_file):
    """
    Load CSV file into Solr.  solr_params are a dictionary of parameters
    sent to solr on the index request.
    """
    file_path = os.path.abspath(csv_file)
    solr_params = {}
    for fieldname in get_multi():
        tag_split = "f.%s.split" % fieldname
        solr_params[tag_split] = 'true'
        tag_separator = "f.%s.separator" % fieldname
        solr_params[tag_separator] = '|'
    solr_params['stream.file'] = file_path
    solr_params['stream.contentType'] = 'text/plain;charset=utf-8'
    solr_params['commit'] = 'true'
    params = urllib.urlencode(solr_params)
    update_url = conf.settings.SOLR_URL + 'update/csv?%s'
    print update_url % params
    print "Loading records into Solr ..."
    try:
        response = urllib.urlopen(update_url % params)
    except IOError:
        raise IOError, 'Unable to connect to the Solr instance.'
    print "Solr response:"
    print response.read()

