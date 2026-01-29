import io
import base64
import logging
import re
import subprocess
import tempfile
from typing import List, Optional, Tuple
import typing
import numpy
import pedalboard
import pedalboard.io
import miniaudio

import soundfile

from freem_bots.configuration import Config
from aiohttp import ClientSession

from enum import Enum

from freem_bots.demoji_wrp import Demoji


class TTSProvider(Enum):
    AZURE = 1
    GCLOUD = 2
    STREAMLABS_POLY = 3
    ESPEAK = 4


class TTSVoiceLanguage(Enum):
    ENGLISH = 1
    SPANISH = 2
    CZECH = 3
    RUSSIAN = 4
    JAPANESE = 5
    SOMALI = 6
    GERMAN = 7
    SWAHILI = 8
    POLISH = 9
    SLOVAK = 10
    WELSH = 11


class TTSVoicelineSpeed(Enum):
    SLOWEST = 0.2
    SLOW = 0.5
    SLOWER = 0.8
    NORMAL = 1.0
    FASTER = 1.2
    FAST = 1.5
    FASTEST = 2.0


class TTSVoicelinePitch(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TTSPause(Enum):
    SHORT = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class TTSVoice(Enum):
    EN_RYAN = (TTSProvider.AZURE, "en-GB-RyanNeural", TTSVoiceLanguage.ENGLISH)
    EN_WILLIAM = (TTSProvider.AZURE, "en-AU-WilliamNeural", TTSVoiceLanguage.ENGLISH)
    EN_CLARA = (TTSProvider.AZURE, "en-CA-ClaraNeural", TTSVoiceLanguage.ENGLISH)
    EN_JENNY = (TTSProvider.AZURE, "en-US-JennyNeural", TTSVoiceLanguage.ENGLISH)
    EN_NEERJA = (TTSProvider.AZURE, "en-IN-NeerjaNeural", TTSVoiceLanguage.ENGLISH)
    EN_ADA = (TTSProvider.GCLOUD, "en-US-Wavenet-C", TTSVoiceLanguage.ENGLISH)

    CS_ANTONIN = (TTSProvider.AZURE, "cs-CZ-AntoninNeural", TTSVoiceLanguage.CZECH)
    CS_VLASTA = (TTSProvider.AZURE, "cs-CZ-VlastaNeural", TTSVoiceLanguage.CZECH)
    CS_JAKUB = (TTSProvider.AZURE, "cs-CZ-Jakub", TTSVoiceLanguage.CZECH)

    RU_DMITRY = (TTSProvider.AZURE, "ru-RU-DmitryNeural", TTSVoiceLanguage.RUSSIAN)
    RU_SVETLANA = (TTSProvider.AZURE, "ru-RU-SvetlanaNeural", TTSVoiceLanguage.RUSSIAN)

    JA_KEITA = (TTSProvider.AZURE, "ja-JP-KeitaNeural", TTSVoiceLanguage.JAPANESE)
    JA_NANAMI = (TTSProvider.AZURE, "ja-JP-NanamiNeural", TTSVoiceLanguage.JAPANESE)

    SO_UBAX = (TTSProvider.AZURE, "so-SO-UbaxNeural", TTSVoiceLanguage.SOMALI)
    DE_CONRAD = (TTSProvider.AZURE, "de-DE-ConradNeural", TTSVoiceLanguage.GERMAN)
    SW_ZURI = (TTSProvider.AZURE, "sw-KE-ZuriNeural", TTSVoiceLanguage.SWAHILI)
    PL_AGNIESZKA = (TTSProvider.AZURE, "pl-PL-AgnieszkaNeural", TTSVoiceLanguage.POLISH)
    SK_VIKTORIA = (TTSProvider.AZURE, "sk-SK-ViktoriaNeural", TTSVoiceLanguage.SLOVAK)
    CY_ALED = (TTSProvider.AZURE, "cy-GB-AledNeural", TTSVoiceLanguage.WELSH)
    ES_ALVARO = (TTSProvider.AZURE, "es-ES-AlvaroNeural", TTSVoiceLanguage.SPANISH)

    EN_XENOWORX = (TTSProvider.STREAMLABS_POLY, "sl-xenoworx", TTSVoiceLanguage.ENGLISH)

    EN_ESPEAK = (TTSProvider.ESPEAK, "en-us", TTSVoiceLanguage.ENGLISH)


class TTSVoicelinePart:
    def __init__(
        self,
        voice: TTSVoice,
        text: str,
        speed: TTSVoicelineSpeed = TTSVoicelineSpeed.NORMAL,
        pitch: TTSVoicelinePitch = TTSVoicelinePitch.MEDIUM,
        prepended_pause: TTSPause | None = None,
    ) -> None:
        self.voice_provider, self.voice_name, self.voice_language = voice.value
        self.text = Demoji().remove_emojis(text)
        self.speed = speed
        self.pitch = pitch
        self.prepended_pause = prepended_pause
        self.ssml_part = self._assemble_ssml_part()
        self.ssml_full = self.assemble_ssml_full(self.ssml_part)

    def _assemble_ssml_part(self) -> str:
        escaped_text = self._escape_text(self.text)

        assembled: str = ""

        if self.voice_provider == TTSProvider.AZURE:
            # open voice name
            assembled += f'<voice name="{self.voice_name}">'
            # open speed, pitch
            assembled += (
                f'<prosody rate="{self.speed.value}" pitch="{self.pitch.value}">'
            )

            # insert pause if applicable
            if self.prepended_pause is not None:
                assembled += f'<break strength="{self.prepended_pause.value}" />'

            # insert text
            assembled += escaped_text

            # close speed, pitch
            assembled += "</prosody>"
            # close voice name
            assembled += "</voice>"
        elif self.voice_provider == TTSProvider.GCLOUD:
            # open voice name
            assembled += f'<voice name="{self.voice_name}">'
            # open speed, pitch
            assembled += f'<prosody rate="{int(self.speed.value * 100)}%" pitch="{self.pitch.value}">'

            # insert pause if applicable
            if self.prepended_pause is not None:
                assembled += f'<break strength="{self.prepended_pause.value}" />'
            # insert text
            assembled += escaped_text

            # close speed, pitch
            assembled += "</prosody>"
            # close voie name
            assembled += "</voice>"
        elif self.voice_provider == TTSProvider.STREAMLABS_POLY:
            assembled += self.text + " "
        elif self.voice_provider == TTSProvider.ESPEAK:
            assembled += self.text + " "
        else:
            raise NotImplementedError()
        return assembled

    @staticmethod
    def _scrub_duplicate_voice_definitions(input_ssml: str) -> str:
        # find all voice starts
        opening_matches: List[Tuple[int, Optional[str]]] = []
        for re_match in re.finditer(r"<voice name=\"(?P<voice>.*?)\">", input_ssml):
            start = re_match.start()
            voice: Optional[str] = re_match.group("voice")
            opening_matches.append((start, voice))

        closing_match_positions: List[int] = []
        for re_match in re.finditer(r"</voice>", input_ssml):
            start = re_match.start()
            closing_match_positions.append(start)

        marked_opening_matches_for_removal: List[Tuple[int, Optional[str]]] = []

        last_match: Optional[Tuple[int, Optional[str]]] = None
        for opening_match in opening_matches:
            if last_match is not None and last_match[1] == opening_match[1]:  # pylint:disable=unsubscriptable-object
                # same voice, can remove here
                marked_opening_matches_for_removal.append(opening_match)
            last_match = opening_match

        marked_closing_matches_for_removal = []
        for marked_opening_match_for_removal in marked_opening_matches_for_removal:
            # need to remove the previous close
            max_previous_close = None
            for close in closing_match_positions:
                if (
                    close >= marked_opening_match_for_removal[0]
                ):  # this close is after our current open, we can keep it
                    continue
                if max_previous_close is None or close > max_previous_close:
                    max_previous_close = close
            if max_previous_close is not None:
                marked_closing_matches_for_removal.append(max_previous_close)

        ranges_marked_for_removal = []
        for marked_opening_match in marked_opening_matches_for_removal:
            start_position = marked_opening_match[0]
            end_position = start_position + len(
                f'<voice name="{marked_opening_match[1]}">'
            )
            ranges_marked_for_removal.append([start_position, end_position])
        for marked_closing_position in marked_closing_matches_for_removal:
            start_position = marked_closing_position
            end_position = start_position + len("</voice>")
            ranges_marked_for_removal.append([start_position, end_position])

        # now, change the input string to char array, replace the removed ranges with None and recombine without these
        input_text_arr = typing.cast(List[Optional[str]], list(input_ssml))
        for range_to_remove in ranges_marked_for_removal:
            for i in range(range_to_remove[0], range_to_remove[1]):
                input_text_arr[i] = None
        output_ssml = "".join([char for char in input_text_arr if char is not None])
        return output_ssml

    def assemble_ssml_full(self, inner_part: Optional[str] = None) -> str:
        if inner_part is None:
            inner_part = self._assemble_ssml_part()

        if self.voice_provider == TTSProvider.AZURE:
            full_ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">{inner_part}</speak>'
        elif self.voice_provider == TTSProvider.GCLOUD:
            full_ssml = f"<speak>{inner_part}</speak>"
        elif self.voice_provider == TTSProvider.STREAMLABS_POLY:
            full_ssml = inner_part
        elif self.voice_provider == TTSProvider.ESPEAK:
            full_ssml = inner_part
        else:
            raise NotImplementedError()
        full_ssml = TTSVoicelinePart._scrub_duplicate_voice_definitions(full_ssml)
        return full_ssml

    def _escape_text(self, text: str) -> str:
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return text

    @staticmethod
    def join_parts(parts: "List[TTSVoicelinePart]") -> str:
        if len(parts) == 0:
            raise Exception("No parts given, nothing to produce")
        initial_provider = parts[0].voice_provider
        for i in range(1, len(parts)):
            if parts[i].voice_provider != initial_provider:
                raise Exception("Cannot use different providers in one voiceline")
        if len(parts) == 1:
            return parts[0].ssml_full
        return parts[0].assemble_ssml_full("".join([part.ssml_part for part in parts]))


class TTSVoiceline:
    def __init__(
        self,
        parts: List[TTSVoicelinePart],
        effects: List[pedalboard.Plugin] | None = None,
    ) -> None:
        self.parts = parts
        self.provider = self.parts[0].voice_provider
        self.ssml = self._get_ssml_for_parts()
        self.effects = [] if effects is None else effects

    def _get_ssml_for_parts(self) -> str:
        return TTSVoicelinePart.join_parts(self.parts)


class TTS:
    def __init__(self, configuration: Config) -> None:
        self._logger = logging.getLogger("tts")
        self.configuration = configuration

    async def get_audio_bytes(
        self, voiceline: TTSVoiceline, target_sample_rate: int = 96000
    ) -> bytes:
        if voiceline.provider == TTSProvider.AZURE:
            tts_bytes = await self._get_audio_bytes_azure(
                voiceline.ssml, target_sample_rate
            )
            was_stereo = True
        elif voiceline.provider == TTSProvider.GCLOUD:
            tts_bytes = await self._get_audio_bytes_gcloud(
                voiceline.ssml, target_sample_rate
            )
            was_stereo = False
        elif voiceline.provider == TTSProvider.STREAMLABS_POLY:
            tts_bytes = await self._get_audio_bytes_streamlabs_poly(
                voiceline.ssml, target_sample_rate
            )
            was_stereo = False
        elif voiceline.provider == TTSProvider.ESPEAK:
            tts_bytes = await self._get_audio_bytes_espeak(
                voiceline.ssml, target_sample_rate
            )
            was_stereo = False
        else:
            raise NotImplementedError()
        with_effects = await self._apply_effects(tts_bytes, voiceline.effects)
        prepared = await self._convert_to_discord_bytes(with_effects, was_stereo)
        return prepared

    async def _get_audio_bytes_azure(self, ssml: str, target_sample_rate: int) -> bytes:
        if self.configuration.azure_token is None:
            raise Exception("Cannot get audio from Azure, no Azure token configured")
        if self.configuration.azure_location is None:
            raise Exception("Cannot get audio from Azure, no Azure location configured")

        url = f"https://{self.configuration.azure_location}.tts.speech.microsoft.com/cognitiveservices/v1"
        output_format = "riff-48khz-16bit-mono-pcm"
        async with ClientSession() as session:
            self._logger.info(
                "Making request to Azure TTS endpoint, format %s", output_format
            )
            async with session.post(
                url=url,
                headers={
                    "Ocp-Apim-Subscription-Key": self.configuration.azure_token,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": output_format,
                },
                data=ssml,
            ) as response:
                self._logger.info("Got response from Azure TTS endpoint")
                response_bytes = await response.read()
                return response_bytes

    async def _get_audio_bytes_gcloud(
        self, ssml: str, target_sample_rate: int
    ) -> bytes:
        if self.configuration.gcloud_voice_key is None:
            raise Exception("Cannot get audio from Azure, no GCloud API key configured")

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.configuration.gcloud_voice_key}"
        output_format = "LINEAR16"
        async with ClientSession() as session:
            self._logger.info(
                "Making request to GCloud TTS endpoint, format %s", output_format
            )
            async with session.post(
                url=url,
                json={
                    "input": {"ssml": ssml},
                    "voice": {
                        "languageCode": "en-us",
                        "name": "en-US-Wavenet-C",
                        "ssmlGender": "FEMALE",
                    },
                    "audioConfig": {"audioEncoding": output_format},
                },
            ) as response:
                self._logger.info("Got response from GCloud TTS endpoint")
                response_json = await response.json()
                response_base64 = response_json["audioContent"]
                response_bytes = base64.b64decode(response_base64)
                return response_bytes

    async def _get_audio_bytes_streamlabs_poly(
        self, text: str, target_sample_rate: int
    ) -> bytes:
        text = text.strip()

        signing_url = "https://us-central1-sunlit-context-217400.cloudfunctions.net/streamlabs-tts"
        async with ClientSession() as session:
            self._logger.info("Making request to Streamlabs signing endpoint")
            mp3_url = ""
            async with session.post(
                url=signing_url,
                json={"text": text, "voice": "Raveena"},
            ) as response:
                self._logger.info("Got response from Streamlabs signing endpoint")
                response_json = await response.json()
                response_success = response_json["success"]
                if not response_success:
                    raise Exception("Streamlabs TTS signature failure")
                mp3_url = response_json["speak_url"]
            async with session.get(mp3_url) as response:
                self._logger.info("Got response from Streamlabs TTS endpoint")
                mp3_data = await response.read()
                wav_data = self._convert_mp3_to_wav(mp3_data, target_sample_rate)
                return wav_data

    async def _get_audio_bytes_espeak(
        self, text: str, target_sample_rate: int
    ) -> bytes:
        text = text.strip()

        self._logger.info("Generating audio with espeak-ng")
        try:
            result = subprocess.run(
                ["espeak-ng", "-v", "en-us", "--stdout"],
                input=text.encode("utf-8"),
                capture_output=True,
                check=True,
            )
            espeak_wav_bytes = result.stdout
            self._logger.info("Generated audio with espeak-ng")

            # Resample to target sample rate
            resampled_wav = self._resample_wav(espeak_wav_bytes, target_sample_rate // 4)
            return resampled_wav
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate audio with espeak-ng: {e}") from e
        except FileNotFoundError as e:
            raise RuntimeError("espeak-ng not found. Please install espeak-ng.") from e

    def _convert_mp3_to_wav(self, mp3_bytes: bytes, sample_rate: int) -> bytes:
        n_channels = 1
        output_format = miniaudio.SampleFormat.SIGNED24

        try:
            decoded_mp3 = miniaudio.decode(
                mp3_bytes,
                output_format=output_format,
                nchannels=n_channels,
                sample_rate=sample_rate,
            )
        except miniaudio.MiniaudioError as e:
            raise RuntimeError(f"Failed to decode MP3: {e}") from e

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
            miniaudio.wav_write_file(temp_file.name, decoded_mp3)
            temp_file.seek(0)
            wav_bytes = temp_file.read()
        return wav_bytes

    def _resample_wav(self, wav_bytes: bytes, sample_rate: int) -> bytes:
        n_channels = 1
        output_format = miniaudio.SampleFormat.SIGNED16

        try:
            decoded_wav = miniaudio.decode(
                wav_bytes,
                output_format=output_format,
                nchannels=n_channels,
                sample_rate=sample_rate,
            )
        except miniaudio.MiniaudioError as e:
            raise RuntimeError(f"Failed to resample WAV: {e}") from e

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
            miniaudio.wav_write_file(temp_file.name, decoded_wav)
            temp_file.seek(0)
            resampled_bytes = temp_file.read()
        return resampled_bytes

    async def _apply_effects(
        self, input_audio: bytes, effects: list[pedalboard.Plugin]
    ) -> bytes:
        with io.BytesIO(input_audio) as input_audio_file:
            with pedalboard.io.ReadableAudioFile(input_audio_file) as pb_file:
                pb_audio = pb_file.read(pb_file.frames)
                pb_samplerate = pb_file.samplerate
                board = pedalboard.Pedalboard(effects)
                affected = board(pb_audio, pb_samplerate)

                with io.BytesIO() as output_audio_file:
                    with soundfile.SoundFile(
                        output_audio_file,
                        mode="w",
                        samplerate=int(pb_samplerate),
                        channels=1,
                        subtype="PCM_24",
                        format="WAV",
                    ) as sf_file:
                        sf_file.write(
                            affected.reshape(
                                affected.shape[1],
                            )
                        )
                    output_audio_file.seek(0)
                    riff_bytes = output_audio_file.read()
                    return riff_bytes

    async def _convert_to_discord_bytes(
        self, audio_bytes: bytes, was_stereo: bool
    ) -> bytes:
        with io.BytesIO(audio_bytes) as audio_file:
            audio_file.name = "audio.wav"
            (audio, _) = soundfile.read(audio_file, dtype="int16")
            stacked = numpy.stack(
                [audio, audio] if was_stereo else [audio, audio, audio, audio], axis=1
            )
            return stacked.tobytes()
