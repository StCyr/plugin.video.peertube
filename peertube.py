# A Kodi Addon to play video hosted on the peertube service (http://joinpeertube.org/)
#
# TODO: - Delete downloaded files by default
#       - Allow people to choose if they want to keep their download after watching?
#       - Make sure we are seeding when downloading and watching
#       - When downloaded torrents are kept, do we want to seed them all the time,
#         or only when the addon is running, or only when kodi is playing one,...?
#       - Do sanity checks on received data
#       - Handle languages better (with .po files)

import time, sys
import urllib2, json
from urlparse import parse_qsl
import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs
import AddonSignals

class PeertubeAddon():
    """
    Main class of the addon
    """

    def __init__(self, plugin, plugin_id):
        """
        Initialisation of the PeertubeAddon class
        :param: None
        :return: None
        """

        xbmc.log('PeertubeAddon: Initialising', xbmc.LOGDEBUG)
 
        # Save addon URL and ID
        self.plugin_url = plugin
        self.plugin_id = plugin_id

        # Get an Addon instance
        addon = xbmcaddon.Addon()

        # Select preferred instance by default
        self.selected_inst = addon.getSetting('preferred_instance') 

        # Get the number of videos to show per page 
        # TODO: Why doesn't it work?
        #self.items_per_page = addon.getSetting('items_per_page')
        self.items_per_page = 20

        # Nothing to play at initialisation
        self.play = 0
        self.torrent_name = ''
        
        return None

    def create_list(self, data, start):
        """
        Create an array of xmbcgui.ListIten's to be displayed as a folder in Kodi's UI
        :param videos, start: dict, str
        :result listing: dict
        """

        # Create a list for our items
        listing = []

        # Return when no results are found
        if data['total'] == 0:
            xbmc.log('PeertubeAddon: No result found', xbmc.LOGDEBUG)
            return
        else:
            xbmc.log('PeertubeAddon: Found ' + str(data['total']) + ' results', xbmc.LOGDEBUG)
        
        # Insert a 'Previous' button when start > 0 
        # TODO: See if icon can be changed here and for the "Next" button (by an arrow for example)
        if int(start) > 0:
            start = int(start) - self.items_per_page 
            list_item = xbmcgui.ListItem(label='Previous')
            url = '{0}?action=browse&start={1}'.format(self.plugin_url, str(start))
            listing.append((url, list_item, True))

        # Create a list for our items.
        for item in data['data']:

            # Create a list item with a text label
            list_item = xbmcgui.ListItem(label=item['name'])
        
            # Add thumbnail
            list_item.setArt({'thumb': self.selected_inst + '/' + item['thumbnailPath']})

            # Set a fanart image for the list item.
            #list_item.setProperty('fanart_image', item['thumb'])

            # Compute media info from item's metadata
            info = {'title': item['name'],
                    'playcount': item['views'],
                    'plotoutline': item['description'],
                    'duration': item['duration']
                    }

            # For videos, add a rating based on likes and dislikes
            if item['likes'] > 0 or item['dislikes'] > 0:
                info['rating'] = item['likes']/(item['likes'] + item['dislikes'])

            # Set additional info for the list item.
            list_item.setInfo('video', info) 

            # This is mandatory for playable items!
            list_item.setProperty('IsPlayable', 'true')

            # Find smallest file's torrentUrl
            # TODO: Get the best quality torrent given settings and/or available bandwidth
            #       See how they do that in the peerTube client's code 
            min_size = -1
            resp = urllib2.urlopen(self.selected_inst + '/api/v1/videos/' + item['uuid'])
            metadata = json.load(resp)
            for f in metadata['files']:
              if f['size'] < min_size or min_size == -1:
                torrent_url = f['torrentUrl'] 

            # Add our item to the listing as a 3-element tuple.
            url = '{0}?action=play&url={1}'.format(self.plugin_url, torrent_url)
            listing.append((url, list_item, False))

        # Insert a 'Next' button when there are more videos to list
        if data['total'] > ( int(start) + 1 ) * self.items_per_page:
            start = int(start) + self.items_per_page 
            list_item = xbmcgui.ListItem(label='Next')
            url = '{0}?action=browse&start={1}'.format(self.plugin_url, str(start))
            listing.append((url, list_item, True))

        return listing

    def search_videos(self, start):
        """
        Search for videos on selected instance
        :param start: string
        :result: None
        """

        # Show a 'Search videos' dialog
        search = xbmcgui.Dialog().input(heading='Search videos on ' + self.selected_inst, type=xbmcgui.INPUT_ALPHANUM)
        # Go back to main menu when user cancels
        if not search:
            self.main_menu()

        # Search for videos on selected PeerTube instance
        # TODO: Make count configurable
        #       Sort videos by rating ( + make the sort method configurabe)
        xbmc.log('PeertubeAddon: Searching for videos on instance ' + self.selected_inst, xbmc.LOGDEBUG)
        req = self.selected_inst + '/api/v1/search/videos?search=' + search + '&count=' + str(self.items_per_page) + '&start=' + start
        try:
            resp = urllib2.urlopen(req)
            videos = json.load(resp)
        except:
            xbmcgui.Dialog().notification('Communication error', 'Error during my search request on ' + self.selected_inst, xbmcgui.NOTIFICATION_ERROR)
            return

        # Create array of xmbcgui.ListItem's
        listing = self.create_list(videos, start)

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.plugin_id, listing, len(listing))
        xbmcplugin.endOfDirectory(self.plugin_id)
        
    def list_videos(self, start):
        """
        Create the list of playable videos in the Kodi interface.
        :param start: string
        :return: None
        """

        # Get the list of videos published by the instance
        # TODO: Make count configurable
        #       Sort videos by rating ( + make the sort method configurabe)
        xbmc.log('PeertubeAddon: Listing videos from instance ' + self.selected_inst, xbmc.LOGDEBUG)
        req = self.selected_inst + '/api/v1/videos?count=' + str(self.items_per_page) + '&start=' + start
        try:
            resp = urllib2.urlopen(req)
            videos = json.load(resp)
        except: 
            xbmcgui.Dialog().notification('Communication error', 'Error during my request to ' + self.selected_inst, xbmcgui.NOTIFICATION_ERROR)
            return

        # Create array of xmbcgui.ListItem's
        listing = self.create_list(videos, start)

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.plugin_id, listing, len(listing))
        xbmcplugin.endOfDirectory(self.plugin_id)

    def play_video_continue(self, data):
        """
        Callback function to let the play_video function resume when the PeertubeDownloader
            has downloaded all the torrent's metadata
        :param data: dict
        :return: None
        """

        xbmc.log('PeertubeAddon: Received metadata_downloaded signal, will start playing media', xbmc.LOGDEBUG)
        self.play = 1    
        self.torrent_f = data['file']

        return

    def play_video(self, torrent_url):
        """
        Start the torrent's download and play it while being downloaded
        :param torrent_url: str
        :return: None
        """

        xbmc.log('PeertubeAddon: playing video ' + torrent_url, xbmc.LOGDEBUG)
        # Start a downloader thread
        AddonSignals.sendSignal('start_download', {'url': torrent_url})

        # Wait until the PeerTubeDownloader has downloaded all the torrent's metadata + a little bit more
        # TODO: Add a timeout
        AddonSignals.registerSlot('plugin.video.peertube', 'metadata_downloaded', self.play_video_continue)
        while self.play == 0:
            xbmc.sleep(1000)
        xbmc.sleep(3000)

        # Pass the item to the Kodi player for actual playback.
        play_item = xbmcgui.ListItem(path=self.torrent_f)
        xbmcplugin.setResolvedUrl(self.plugin_id, True, listitem=play_item)

    def main_menu(self):
        """
        """

        # Create a list for our items.
        listing = []

        # 1st menu entry
        list_item = xbmcgui.ListItem(label='Browse selected instance')
        url = '{0}?action=browse&start=0'.format(self.plugin_url)
        listing.append((url, list_item, True))

        # 2nd menu entry
        list_item = xbmcgui.ListItem(label='Search on selected instance')
        url = '{0}?action=search&start=0'.format(self.plugin_url)
        listing.append((url, list_item, False))

        # 3rd menu entry
        list_item = xbmcgui.ListItem(label='Select other instance')
        url = '{0}?action=select_inst&start=0'.format(self.plugin_url)
        listing.append((url, list_item, False))

        # Add our listing to Kodi.
        xbmcplugin.addDirectoryItems(self.plugin_id, listing, len(listing))

        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(self.plugin_id, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_id)

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
            if params['action'] == 'browse':
                # List videos on selected instance
                self.list_videos(params['start'])
            elif params['action'] == 'search':
                # Search for videos on selected instance
                self.search_videos(params['start'])
            elif params['action'] == 'select_inst':
                # Select another peerTube instance
                self.select_instance(params['start'])
            elif params['action'] == 'play':
                # Play video from provided URL.
                self.play_video(params['url'])
        else:
            # Display the addon's main menu when the plugin is called from Kodi UI without any parameters
            self.main_menu()

if __name__ == '__main__':

    # Initialise addon
    addon = PeertubeAddon(sys.argv[0], int(sys.argv[1]))
    # Call the router function and pass the plugin call parameters to it.
    addon.router(sys.argv[2])
