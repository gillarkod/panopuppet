__author__ = 'takeshi'

from pano.settings import PUPPETMASTER_CERTIFICATES, PUPPETMASTER_VERIFY_SSL, PUPPETMASTER_CLIENTBUCKET_SHOW, \
    PUPPETMASTER_CLIENTBUCKET_HOST
from pano.settings import PUPPETDB_CERTIFICATES, PUPPETDB_VERIFY_SSL, PUPPETDB_HOST

from pano.puppetdb.puppetdb import api_get as pdb_api_get
import requests

requests.packages.urllib3.disable_warnings()

import hashlib


def get_hash(data):
    m = hashlib.md5()
    m.update(data.encode('utf-8'))
    return m.hexdigest()


def get_file(certname, environment, rtitle, rtype, md5sum_from=None, md5sum_to=None, diff=False, file_status='from'):
    # If Clientbucket is enabled continue else return False
    if not PUPPETMASTER_CLIENTBUCKET_SHOW:
        return False

    headers_clientbucket = {
        'Accept': 's',
    }
    if file_status == 'from' and md5sum_from:
        md5sum = md5sum_from.replace('{md5}', '')
    elif file_status == 'to' and md5sum_to:
        md5sum = md5sum_to.replace('{md5}', '')
    else:
        return False
    url_clientbucket = PUPPETMASTER_CLIENTBUCKET_HOST + environment + '/file_bucket_file/md5/' + md5sum
    resp_clientbucket = requests.head(url_clientbucket,
                                      headers=headers_clientbucket,
                                      verify=PUPPETMASTER_VERIFY_SSL,
                                      cert=PUPPETMASTER_CERTIFICATES)

    if resp_clientbucket.status_code != 200:
        # Check if theres a resource available for the latest file available
        if file_status == 'to':
            resp_pdb = pdb_api_get(path='nodes/' + certname + '/resources/' + rtype + '/' + rtitle,
                                   verify=PUPPETDB_VERIFY_SSL)
            if resp_pdb:
                resource_data = resp_pdb[0]
                if 'content' in resource_data['parameters']:
                    prepend_text = 'This file with MD5 %s was found in PuppetDB Resources.\n\n' % (
                    get_hash(resource_data['parameters']['content']))
                    return prepend_text + resource_data['parameters']['content']
                # Todo get the data from source file - Request from Puppetmaster
                elif 'source' in resource_data['parameters']:
                    return False
            else:
                return False
        else:
            return False
    else:
        resp_clientbucket = requests.get(url_clientbucket,
                                         headers=headers_clientbucket,
                                         verify=PUPPETMASTER_VERIFY_SSL,
                                         cert=PUPPETMASTER_CERTIFICATES)
        prepend_text = 'This file with MD5 %s was found in Filebucket.\n\n' % (md5sum)
        return prepend_text + resp_clientbucket.text