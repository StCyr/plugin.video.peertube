import libtorrent
import time, sys
import xbmcvfs
import AddonSignals
from threading import Thread

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

class PeertubeService():
    """
    """

    def download_torrent(self, data):
        """
        Start a downloader thread to download torrent specified by data['magnet_f']
        :param data: dict
        :return: None
        """

        downloader = PeertubeDownloader(data['magnet_f']) 
        downloader.start()

    def run(self):
        """
        """

        # Launch the download_torrent callback function when the 'start_download' signal is received
        AddonSignals.registerSlot('plugin.video.peertube', 'start_download', self.download_torrent)

        # Monitor Kodi's shutdown signal
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if monitor.waitForAbort(1):
                # Abort was requested while waiting. We must exit
                # TODO: I must delete all temp files before exiting
                break


if __name__ == '__main__':
    # Start a peertubeService instance
    service = PeertubeService()
    service.run()
