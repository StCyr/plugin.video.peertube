import libtorrent
import time, sys
import xbmc, xbmcvfs
import AddonSignals
from threading import Thread

class PeertubeDownloader(Thread):
    """
    A class to download peertube torrents in the background
    """

    def __init__(self, magnet_f):
        """
        :param magnet_f: str
        :return: None
        """
        Thread.__init__(self)
        self.magnet_f = magnet_f

    def run(self):
        """
        Download the torrent specified by self.magnet_f
        :param: None
        :return: None
        """

        xbmc.log('PeertubeDownloader: Starting a torrent download', xbmc.LOGINFO)
        # Open bitTorrent session
        ses = libtorrent.session()
        ses.listen_on(6881, 6891)

        # Read magnet's data
        f = xbmcvfs.File(self.magnet_f, 'r')
        magnet = f.read()

        # Add torrent
        xbmc.log('PeertubeDownloader: Adding torrent ' + magnet, xbmc.LOGINFO)
        fpath = xbmc.translatePath('special://temp')
        h = ses.add_torrent({'url': magnet, 'save_path': fpath})

        # Set sequential mode to allow watching while downloading
        h.set_sequential_download(True)

        # Download torrent
        signal_sent = 0
        while not h.is_seed():
            xbmc.sleep(1000)
            s = h.status()
            # Inform addon that all the metadata has been downloaded and that it may start playing the torrent
            if s.state >=3 and signal_sent == 0:
                xbmc.log('PeertubeDownloader: Received all torrent metadata, notifying PeertubeAddon', xbmc.LOGINFO)
                AddonSignals.sendSignal('metadata_downloaded', {'name': h.name()} )
                signal_sent = 1

        # Everything is done
        return

class PeertubeService():
    """
    """

    def __init__(self):
        """
        PeertubeService initialisation function
        """

        xbmc.log('PeertubeService: Initialising', xbmc.LOGINFO)
        # Create our temporary directory 
        fpath = xbmc.translatePath('special://temp') + '/plugin.video.peertube'
        if not xbmcvfs.exists(fpath):
            xbmcvfs.mkdir(fpath)

    def download_torrent(self, data):
        """
        Start a downloader thread to download torrent specified by data['magnet_f']
        :param data: dict
        :return: None
        """

        xbmc.log('PeertubeService: Received a start_download signal', xbmc.LOGINFO)
        downloader = PeertubeDownloader(data['magnet_f']) 
        downloader.start()
   
        return

    def run(self):
        """
        Main loop of the PeertubeService class, registring the start_download signal to start a 
            peertubeDownloader thread when needed, and exit when Kodi is shutting down
        """

        # Launch the download_torrent callback function when the 'start_download' signal is received
        AddonSignals.registerSlot('plugin.video.peertube', 'start_download', self.download_torrent)

        # Monitor Kodi's shutdown signal
        xbmc.log('PeertubeService: service started, Waiting for signals', xbmc.LOGINFO)
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if monitor.waitForAbort(1):
                # Abort was requested while waiting. We must exit
                # TODO: I must delete all temp files before exiting
                break
       
        return


if __name__ == '__main__':
    # Start a peertubeService instance
    xbmc.log('PeertubeService: Starting', xbmc.LOGINFO)
    service = PeertubeService()
    service.run()
    xbmc.log('PeertubeService: Exiting', xbmc.LOGINFO)
