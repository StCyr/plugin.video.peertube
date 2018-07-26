import time
import xbmc

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    
    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We must exit
            break
