import audioop
import io
import wave

class AudioData(object):

    def __init__(self, frame_data, sample_rate, sample_width):
        assert sample_rate > 0, "Sample rate must be a positive integer"
        assert (
            sample_width % 1 == 0 and 1 <= sample_width <= 4
        ), "Sample width must be between 1 and 4 inclusive"
        self.frame_data = frame_data
        self.sample_rate = sample_rate
        self.sample_width = int(sample_width)

    def get_segment(self, start_ms=None, end_ms=None):
        """
        Returns a new ``AudioData`` instance, trimmed to a given time interval. In other words, an ``AudioData`` instance with the same audio data except starting at ``start_ms`` milliseconds in and ending ``end_ms`` milliseconds in.

        If not specified, ``start_ms`` defaults to the beginning of the audio, and ``end_ms`` defaults to the end.
        """
        assert (
            start_ms is None or start_ms >= 0
        ), "``start_ms`` must be a non-negative number"
        assert end_ms is None or end_ms >= (
            0 if start_ms is None else start_ms
        ), "``end_ms`` must be a non-negative number greater or equal to ``start_ms``"
        if start_ms is None:
            start_byte = 0
        else:
            start_byte = int(
                (start_ms * self.sample_rate * self.sample_width) // 1000
            )
        if end_ms is None:
            end_byte = len(self.frame_data)
        else:
            end_byte = int(
                (end_ms * self.sample_rate * self.sample_width) // 1000
            )
        return AudioData(
            self.frame_data[start_byte:end_byte],
            self.sample_rate,
            self.sample_width,
        )
    
    def get_raw_data(self, convert_rate=None, convert_width=None):
        """
        Returns a byte string representing the raw frame data for the audio represented by the ``AudioData`` instance.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        Writing these bytes directly to a file results in a valid `RAW/PCM audio file <https://en.wikipedia.org/wiki/Raw_audio_format>`__.
        """
        assert (
            convert_rate is None or convert_rate > 0
        ), "Sample rate to convert to must be a positive integer"
        assert convert_width is None or (
            convert_width % 1 == 0 and 1 <= convert_width <= 4
        ), "Sample width to convert to must be between 1 and 4 inclusive"

        raw_data = self.frame_data

        # make sure unsigned 8-bit audio (which uses unsigned samples) is handled like higher sample width audio (which uses signed samples)
        if self.sample_width == 1:
            raw_data = audioop.bias(
                raw_data, 1, -128
            )  # subtract 128 from every sample to make them act like signed samples

        # resample audio at the desired rate if specified
        if convert_rate is not None and self.sample_rate != convert_rate:
            raw_data, _ = audioop.ratecv(
                raw_data,
                self.sample_width,
                1,
                self.sample_rate,
                convert_rate,
                None,
            )

        # convert samples to desired sample width if specified
        if convert_width is not None and self.sample_width != convert_width:
            if (
                convert_width == 3
            ):  # we're converting the audio into 24-bit (workaround for https://bugs.python.org/issue12866)
                raw_data = audioop.lin2lin(
                    raw_data, self.sample_width, 4
                )  # convert audio into 32-bit first, which is always supported
                try:
                    audioop.bias(
                        b"", 3, 0
                    )  # test whether 24-bit audio is supported (for example, ``audioop`` in Python 3.3 and below don't support sample width 3, while Python 3.4+ do)
                except (
                    audioop.error
                ):  # this version of audioop doesn't support 24-bit audio (probably Python 3.3 or less)
                    raw_data = b"".join(
                        raw_data[i + 1 : i + 4]
                        for i in range(0, len(raw_data), 4)
                    )  # since we're in little endian, we discard the first byte from each 32-bit sample to get a 24-bit sample
                else:  # 24-bit audio fully supported, we don't need to shim anything
                    raw_data = audioop.lin2lin(
                        raw_data, self.sample_width, convert_width
                    )
            else:
                raw_data = audioop.lin2lin(
                    raw_data, self.sample_width, convert_width
                )

        # if the output is 8-bit audio with unsigned samples, convert the samples we've been treating as signed to unsigned again
        if convert_width == 1:
            raw_data = audioop.bias(
                raw_data, 1, 128
            )  # add 128 to every sample to make them act like unsigned samples again

        return raw_data
    
    def get_wav_data(self, convert_rate=None, convert_width=None, nchannels=1):
        """
        Returns a byte string representing the contents of a WAV file containing the audio represented by the ``AudioData`` instance.

        If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.

        If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.

        Writing these bytes directly to a file results in a valid `WAV file <https://en.wikipedia.org/wiki/WAV>`__.
        """
        raw_data = self.get_raw_data(convert_rate, convert_width)
        sample_rate = (
            self.sample_rate if convert_rate is None else convert_rate
        )
        sample_width = (
            self.sample_width if convert_width is None else convert_width
        )

        # generate the WAV file contents
        with io.BytesIO() as wav_file:
            wav_writer = wave.open(wav_file, "wb")
            try:  # note that we can't use context manager, since that was only added in Python 3.4
                wav_writer.setframerate(sample_rate)
                wav_writer.setsampwidth(sample_width)
                wav_writer.setnchannels(nchannels)
                wav_writer.writeframes(raw_data)
                wav_data = wav_file.getvalue()
            finally:  # make sure resources are cleaned up
                wav_writer.close()
        return wav_data
