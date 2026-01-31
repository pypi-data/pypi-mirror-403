import time

import labrecorder
import pylsl
import numpy as np

from threading import Thread

def record():
    streams = pylsl.resolve_streams()
    with labrecorder.Recording("out.xdf", streams):
        input("Recording... press Enter to stop\n")

def stream():
    info = pylsl.StreamInfo(name="test", type="EEG", channel_count=64, nominal_srate=1000)
    outlet = pylsl.StreamOutlet(info)
    while True:
        outlet.push_chunk(np.random.rand(64, 100).astype(np.float32))
        time.sleep(0.1)

def main():
    thread = Thread(target=stream, daemon=True)
    thread.start()
    
    record()


if __name__ == "__main__":
    main()
