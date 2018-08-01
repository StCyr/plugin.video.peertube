A kodi addon for watching content hosted on Peertube (http://joinpeertube.org/) 

This code is still proof-of-concept but it works, and you're welcome to improve it.

# Functionalities

* Browse all videos on a PeerTube instance 
* Search for videos on a PeerTube instance (Only supported by 1.0.0-beta10+ instances)
* Select Peertube instance to use (Doesn't work yet)

# User settings

* User definable preferred PeerTube instance 
* Number of videos to display per page
* Sort method to be used when listing videos (Currently, only 'views' and 'likes') 

# Limitations

* This addon doesn't support Webtorrent yet. So, it cannot download/share from/to regular PeerTube clients.
The reason is that it uses the libtorrent python libray which doesn't support it yet (see https://github.com/arvidn/libtorrent/issues/223)
* The addon doesn't delete the downloaded files atm. So, it may fills up your disk 
* Currently, the addon always download the smallest file it can found for any video you want to play. So, video quality is mostly low.

# Requirements

* Kodi 17 or above
* libtorrent python bindings (https://libtorrent.org/). On Debian type `apt install python-libtorrent` as root.
