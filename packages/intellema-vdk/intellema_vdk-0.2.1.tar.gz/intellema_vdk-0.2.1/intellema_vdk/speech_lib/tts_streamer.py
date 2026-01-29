import os
import queue
import threading
import time
import pyaudio
from together import Together


class TTSStreamer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Together API Key is missing. Set TOGETHER_API_KEY env var."
            )

        self.client = Together(api_key=self.api_key)

        # Audio Config
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16, channels=1, rate=24000, output=True
        )

        # Queues
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()

        # State
        self.text_buffer = ""
        self.is_running = True
        self.playback_finished = threading.Event()

        # Start Threads
        self.fetcher_thread = threading.Thread(target=self._tts_fetcher, daemon=True)
        self.player_thread = threading.Thread(target=self._audio_player, daemon=True)

        self.fetcher_thread.start()
        self.player_thread.start()

    def feed(self, text_chunk):
        """Feed text tokens from LLM."""
        if not self.is_running or not text_chunk:
            return

        self.text_buffer += text_chunk
        sentence_endings = [".", "!", "?", "\n"]

        for ending in sentence_endings:
            if ending in self.text_buffer:
                parts = self.text_buffer.split(ending)

                # Send all complete sentences
                for sentence in parts[:-1]:
                    if sentence.strip():
                        self.text_queue.put(sentence.strip() + ending)

                # Keep the remainder
                self.text_buffer = parts[-1]

    def flush(self):
        """
        Graceful finish: Push remaining text, signal end, and wait for audio to finish playing.
        """
        # 1. Push remaining buffer
        if self.text_buffer.strip():
            self.text_queue.put(self.text_buffer.strip())

        # 2. Signal Fetcher to stop expecting text
        self.text_queue.put(None)

        # 3. Wait for the player to signal it's done
        # We use a timeout to prevent infinite hanging
        self.playback_finished.wait(timeout=10.0)

    def close(self):
        """
        Immediate kill: Stop threads and close audio stream.
        """
        if not self.is_running:
            return

        self.is_running = False

        # Clear queues to unblock threads if they are stuck
        with self.text_queue.mutex:
            self.text_queue.queue.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        try:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
        except Exception:
            pass

    def stop(self):
        """Alias for close"""
        self.close()

    def _tts_fetcher(self):
        while self.is_running:
            try:
                text = self.text_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if text is None:
                self.audio_queue.put(None)  # Signal player to finish
                break

            try:
                response = self.client.audio.speech.create(
                    model="canopylabs/orpheus-3b-0.1-ft",
                    input=text,
                    voice="tara",
                    stream=True,
                    response_format="raw",
                    response_encoding="pcm_s16le",
                )

                for chunk in response:
                    if not self.is_running:
                        break

                    if isinstance(chunk, tuple):
                        if len(chunk) > 1:
                            sub_iterator = chunk[1]
                            # Check if explicitly bytes (non-iterable in this context intended for iteration)
                            if isinstance(sub_iterator, bytes):
                                self._process_audio_bytes(sub_iterator)
                            else:
                                try:
                                    for sub_chunk in sub_iterator:
                                        if isinstance(sub_chunk, bytes):
                                            self._process_audio_bytes(sub_chunk)
                                        elif hasattr(sub_chunk, "content"):
                                            self._process_audio_bytes(sub_chunk.content)
                                        elif hasattr(sub_chunk, "data"):
                                            self._process_audio_bytes(sub_chunk.data)
                                except TypeError:
                                    pass

                    elif hasattr(chunk, "content"):
                        audio_data = chunk.content
                        if audio_data:
                            self._process_audio_bytes(audio_data)

                    elif isinstance(chunk, bytes):
                        self._process_audio_bytes(chunk)

            except Exception as e:
                print(f"TTS Error: {e}")
            finally:
                self.text_queue.task_done()

    def _process_audio_bytes(self, audio_data):
        """Helper to strip headers and push to queue"""
        # Strip WAV header if present (RIFF...WAVE)
        if len(audio_data) >= 44 and audio_data[:4] == b"RIFF":
            audio_data = audio_data[44:]
        self.audio_queue.put(audio_data)

    def _audio_player(self):
        buffer = b""
        while self.is_running:
            try:
                audio_data = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if audio_data is None:
                self.playback_finished.set()
                break

            buffer += audio_data

            if len(buffer) >= 2:
                frame_count = len(buffer) // 2
                bytes_to_play = frame_count * 2
                play_chunk = buffer[:bytes_to_play]
                buffer = buffer[bytes_to_play:]

                try:
                    self.stream.write(play_chunk)
                except OSError:
                    break
