#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import time
import shutil
import traceback
from base64 import b16encode, b32decode

from torrent.helpers.variable import link, symlink, is_rarfile

import requests
#from lib.unrar2 import RarFile

import torrent.clients.rtorrent as TorClient

import mylar
from mylar import logger, helpers

class RTorrent(object):
    def __init__(self):
        self.client = TorClient.TorrentClient()
        if not self.client.connect(mylar.RTORRENT_HOST,
                                   mylar.RTORRENT_USERNAME,
                                   mylar.RTORRENT_PASSWORD):
            logger.error('could not connect to %s, exiting', mylar.RTORRENT_HOST)
            sys.exit(-1)

    def main(self, torrent_hash=None, filepath=None, check=False):

        torrent = self.client.find_torrent(torrent_hash)
        if torrent:
            if check:
                logger.info('Successfully located torrent %s by hash on client. Detailed statistics to follow', torrent_hash)
            else:
                logger.warn("%s Torrent already exists. Not downloading at this time.", torrent_hash)
                return
        else:
            if check:
                logger.warn('Unable to locate torrent with a hash value of %s', torrent_hash)
                return
        
        if filepath:
            loadit = self.client.load_torrent(filepath)
            if loadit:
                torrent_hash = self.get_the_hash(filepath)
            else:
                return

        torrent = self.client.find_torrent(torrent_hash)
        if torrent is None:
            logger.warn("Couldn't find torrent with hash: %s", torrent_hash)
            sys.exit(-1)

        torrent_info = self.client.get_torrent(torrent)
        if check:
            return torrent_info

        if torrent_info['completed']:
            logger.info("Directory: %s", torrent_info['folder'])
            logger.info("Name: %s", torrent_info['name'])
            logger.info("FileSize: %s", helpers.human_size(torrent_info['total_filesize']))
            logger.info("Completed: %s", torrent_info['completed'])
            logger.info("Downloaded: %s", helpers.human_size(torrent_info['download_total']))
            logger.info("Uploaded: %s", helpers.human_size(torrent_info['upload_total']))
            logger.info("Ratio: %s", torrent_info['ratio'])
            #logger.info("Time Started: %s", torrent_info['time_started'])
            logger.info("Seeding Time: %s", helpers.humanize_time(int(time.time()) - torrent_info['time_started']))

            if torrent_info['label']:
                logger.info("Torrent Label: %s", torrent_info['label'])

        #logger.info(torrent_info)
        return torrent_info           

    def get_the_hash(self, filepath):
        import hashlib, StringIO
        import rtorrent.lib.bencode as bencode

        # Open torrent file
        torrent_file = open(filepath, "rb")
        metainfo = bencode.decode(torrent_file.read())
        info = metainfo['info']
        thehash = hashlib.sha1(bencode.encode(info)).hexdigest().upper()
        logger.info('Hash: ' + thehash)
        return thehash