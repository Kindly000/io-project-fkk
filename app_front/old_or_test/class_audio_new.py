import soundcard as sc
import soundfile as sf

class AudioRecorder:
    def __init__(self, filename):
        self.filename = filename
        self.sample_rate = 48000
        self.record_sec_test = 5

    def record_test(self):
        with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(
                samplerate=self.sample_rate) as mic:
            # record audio with loopback from default speaker.
            data = mic.record(numframes=self.sample_rate * self.record_sec_test)

            # change "data=data[:, 0]" to "data=data", if you would like to write audio as multiple-channels.
            sf.write(file=self.filename, data=data[:, 0], samplerate=self.sample_rate)


if __name__ == "__main__":
    try:
        recorder = AudioRecorder("../test.wav")
        recorder.record_test()
    except:
        print("Couldn't open")