# A Kodi Addon to play video hosted on the peertube service (http://joinpeertube.org/)
#
# This is just a Proof-Of-Concept atm but I hope I will be able to make it evolve to
# something worth using.
#
# TODO: - Delete downloaded files by default
#       - Allow people to choose if they want to keep their download after watching?
#       - Make sure we are seeding when downloading and watching
#       - When downloaded torrents are kept, do we want to seed them all the time,
#         or only when the addon is running, or only when kodi is playing one,...?
#       - Do sanity checks on received data

import libtorrent
import time, sys
import urllib2, json
from urlparse import parse_qsl
import AddonSignals
import xbmcgui, xbmcplugin, xbmcvfs
from threading import Thread

# Get the plugin url in plugin:// notation.
__url__ = sys.argv[0]
# Get the plugin handle as an integer number.
__handle__ = int(sys.argv[1])

class PeertubeDownloader(Thread):
    """
    A class to download peertube torrents in the background
    """

    def init(self, magnet_f):
        """
        :param magnet_f: str
        :return: None
        """
        Thread.__init__(self)
        self.magnet_f

    def run(self):
        """
        Download the torrent specified by self.magnet_f
        :param: None
        :return: None
        """

        # Open bitTorrent session
        ses = libtorrent.session()
        ses.listen_on(6881, 6891)

        # Read magnet's data
        f = xbmcvfs.File(self.magnet_f, 'r')
        magnet = f.read()

        # Add torrent
        fpath = xbmc.translatePath('special://temp')
        h = ses.add_torrent({'url': magnet, 'save_path': fpath})

        # Set sequential mode to allow watching while downloading
        h.set_sequential_download(True)

        # Download torrent
        signal_sent = 0
        while not h.is_seed():
            time.sleep(1)
            s = h.status(e)
            # Inform addon that all the metadata has been downloaded and that it may start playing the torrent
            if s.status >=3 and signal_sent == 0:
                AddonSignals.sendSignal('metadata_downloaded', {'name': h.name()} )
                signal_sent = 1

        # Everything is done
        return

class PeertubeAddon():
    """
    Main class of the addon
    """

    def __init__(self):
        """
        """

        # Nothing to play at initialisation
        self.play = 0
        
        return None

    def list_videos(self):
        """
        Create the list of playable videos in the Kodi interface.
        :param: None
        :return: None
        """

        # TODO: Make the instance configurable
        #       Make it actuatly possible to use several instances
        inst = 'https://peertube.cpy.re'

        # Get the list of videos published by the instance
        # TODO: Handle failures
        resp = urllib2.urlopen(inst + '/api/v1/videos')
        videos = json.load(resp)

        # Return when no videos are found
        if videos['total'] == 0:
            return

        # Create a list for our items.
        listing = []
        for video in videos:

            # Create a list item with a text label
            list_item = xbmcgui.ListItem(label=video['name'])
        
            # Add thumbnail
            list_item.setArt({'thumb': inst + '/' + video['thumbnailPath']})

            # Set a fanart image for the list item.
            #list_item.setProperty('fanart_image', video['thumb'])

            # Compute media info from video's metadata
            info = {'title': video['name'],
                    'playcount': video['views'],
                    'plotoutline': video['description'],
                    'duration': video['duration']
                    }

            # Add a rating based on likes and dislikes
            if video['likes'] > 0 or video['dislikes'] > 0:
                info['rating'] = video['likes']/(video['likes'] + video['dislikes'])

            # Set additional info for the list item.
            list_item.setInfo('video', info) 

            # This is mandatory for playable items!
            list_item.setProperty('IsPlayable', 'true')

            # Find smallest file's torrentUrl
            # TODO: Get the best quality torrent given settings and/or available bandwidth
            #       See how they do that in the peerTube client's code 
            min_size = -1
            resp = urllib2.urlopen(inst + '/api/v1/videos/' + video['uuid'])
            metadata = json.load(resp)
            for f in metadata['files']:
              if f['size'] < min_size or min_size == -1:
                magnet = f['magnetUri'] 

            # Save magnet link temporarily.
            tmp_f = xbmc.translatePath('special://temp') + '/plugin.video.peertube/todo'
            f = xbmcvfs.File(tmp_f, 'w')
        f.write(magnet)
        f.close()

        # Add our item to the listing as a 3-element tuple.
        url = '{0}?action=play&magnet={1}'.format(__url__, tmp_f)
        listing.append((url, list_item, False))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
        xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory(__handle__)

    def play_video_continue():
        """
        """

        self.play = 1    
        return

    def play_video(self, magnet_f):
        """
        Start the torrent's download and play it while being downloaded
        :param magnet_f: str
        :return: None
        """

        # Start a downloader thread
        pd = PeertubeDownloader.start(magnet_f)

        # Wait until the PeerTubeDownloader has downloaded all the torrent's metadata + a little bit more
        AddonSignals.RegisterSlot('plugin.video.peertube', 'metadata_downloaded', play_video_continue)
        while self.play == 0:
            xbmc.sleep(1000)
        xbmc.sleep(3000)

        # Pass the item to the Kodi player for actual playback.
        path = fpath + h.name()
        play_item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(__handle__, True, listitem=play_item)

    def router(self, paramstring):
        """
        Router function that calls other functions
        depending on the provided paramstring
        :param paramstring: dict
        :return: None
        """

        # Parse a URL-encoded paramstring to the dictionary of
        # {<parameter>: <value>} elements
        params = dict(parse_qsl(paramstring[1:]))

        # Check the parameters passed to the plugin
        if params:
            # Play a video from a provided URL.
            self.play_video(params['magnet'])
        else:
            # Display the list of videos when the plugin is called from Kodi UI without any parameters
            self.list_videos()

if __name__ == '__main__':

    # Initialise addon
    addon = PeertubeAddon()
    # Call the router function and pass the plugin call parameters to it.
    addon.router(sys.argv[2])
