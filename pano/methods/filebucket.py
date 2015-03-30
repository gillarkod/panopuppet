__author__ = 'takeshi'

from pano.settings import PUPPETMASTER_CERTIFICATES, PUPPETMASTER_VERIFY_SSL, PUPPETMASTER_CLIENTBUCKET_SHOW, \
    PUPPETMASTER_CLIENTBUCKET_HOST
from pano.settings import PUPPETDB_CERTIFICATES, PUPPETDB_VERIFY_SSL

from pano.puppetdb.puppetdb import api_get as pdb_api_get
import requests

requests.packages.urllib3.disable_warnings()

import hashlib
import difflib


def get_hash(data):
    m = hashlib.md5()
    m.update(data.encode('utf-8'))
    return m.hexdigest()


def get_file(certname, environment, rtitle, rtype, md5sum_from=None, md5sum_to=None, diff=False, file_status='from'):
    # If Clientbucket is enabled continue else return False
    def fetch_filebucket(url, method):
        headers = {
            'Accept': 's',
        }
        methods = {'get': requests.get,
                   'head': requests.head,
        }
        if method not in methods:
            print('No can has method: %s' % (method))
            return False
        resp = methods[method](url,
                               headers=headers,
                               verify=PUPPETMASTER_VERIFY_SSL,
                               cert=PUPPETMASTER_CERTIFICATES)
        if resp.status_code != 200:
            return False
        else:
            return resp.text

    def get_resource(certname, rtype, rtitle):
        data = pdb_api_get(path='nodes/' + certname + '/resources/' + rtype + '/' + rtitle,
                           verify=PUPPETDB_VERIFY_SSL,
                           cert=PUPPETDB_CERTIFICATES)
        if not data:
            return False
        else:
            return data


    if not PUPPETMASTER_CLIENTBUCKET_SHOW:
        return False
    if file_status == 'both':
        if md5sum_to and md5sum_from and certname and rtitle and rtype:
            if diff:
                # is the hash from puppetdb resource same as md5sum_to
                hash_matches = False

                md5sum_from = md5sum_from.replace('{md5}', '')
                md5sum_to = md5sum_to.replace('{md5}', '')

                from_url = PUPPETMASTER_CLIENTBUCKET_HOST + environment + '/file_bucket_file/md5/' + md5sum_from
                print(from_url)
                to_url = PUPPETMASTER_CLIENTBUCKET_HOST + environment + '/file_bucket_file/md5/' + md5sum_to
                print(to_url)
                if fetch_filebucket(from_url, 'head') is not False:
                    resource_from = fetch_filebucket(from_url, 'get')
                else:
                    return "Could not find old MD5 %s in Filebucket." % (md5sum_from)
                if fetch_filebucket(to_url, 'head') is not False:
                    resource_to = fetch_filebucket(to_url, 'get')
                # Try puppetdb resources if not found in filebucket.
                else:
                    resource_to = get_resource(certname, rtype, rtitle)
                    if resource_to is False:
                        return "Could not find new MD5 %s in Filebucket or as a PuppetDB Resource." % (md5sum_to)
                    else:
                        print("found new file")
                        resource_to = resource_to[0]
                    if 'content' in resource_to['parameters']:
                        resource_to = resource_to['parameters']['content']
                        hash_of_resource = get_hash(resource_to)
                        if hash_of_resource == md5sum_to:
                            # file from resource matches filebucket md5 hash
                            hash_matches = True
                # now that we have come this far, we have both files.
                # Lets differentiate the shit out of these files.
                from_split_lines = resource_from.split('\n')
                to_split_lines = resource_to.split('\n')
                diff = difflib.unified_diff(from_split_lines, to_split_lines)
                return '\n'.join(list(diff))
            else:
                return False
        else:
            return False

    if file_status == 'from' and md5sum_from:
        md5sum = md5sum_from.replace('{md5}', '')
    elif file_status == 'to' and md5sum_to:
        md5sum = md5sum_to.replace('{md5}', '')
    else:
        return False
    # Creates headers and url from the data we got

    url_clientbucket = PUPPETMASTER_CLIENTBUCKET_HOST + environment + '/file_bucket_file/md5/' + md5sum
    if fetch_filebucket(url_clientbucket, 'head') is False:
        # Check if theres a resource available for the latest file available
        if file_status == 'to':
            resp_pdb = get_resource(certname, rtype, rtitle)
            # we got the data lets give the user the good news.
            if resp_pdb:
                resource_data = resp_pdb[0]
                if 'content' in resource_data['parameters']:
                    prepend_text = 'This file with MD5 %s was found in PuppetDB Resources.\n\n' % (
                        get_hash(resource_data['parameters']['content']))
                    return prepend_text + resource_data['parameters']['content']
                # Todo get the data from source file - Request from Puppetmaster
                elif 'source' in resource_data['parameters']:
                    return
            # the file can't be found as a resource
            else:
                return False
        # We probably don't want to search for resources if its the old file.
        else:
            return False
    else:
        filebucket_results = fetch_filebucket(url_clientbucket, 'get')
        prepend_text = 'This file with MD5 %s was found in Filebucket.\n\n' % (md5sum)
        return prepend_text + filebucket_results