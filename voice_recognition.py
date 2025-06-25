import io
import wave
import tempfile
import os
import threading
import time
import platform
from PyQt6.QtCore import QObject, pyqtSignal
from openai import OpenAI


class VoiceRecognizer(QObject):
    """
    Improved voice recognition class using OpenAI's Whisper API
    """
    transcription_complete = pyqtSignal(str)
    recording_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.audio_frames = []
        self.sample_rate = 16000
        self.channels = 1
        self.recording_thread = None
        self.language = "en"  # Default language is English

        # Initialize OpenAI client
        self.client = None
        try:
            with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
                api_key = file.read().strip()
                self.client = OpenAI(api_key=api_key)

                print(f"Voice recognizer OpenAI client initialized successfully on {platform.system()}")
        except Exception as e:
            print(f"Error initializing OpenAI client for voice recognition: {e}")

    def start_recording(self):
        """Start recording audio"""
        if self.recording:
            return

        self.recording = True
        self.audio_frames = []
        self.recording_status.emit(True)

        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_recording(self):
        """Stop recording and transcribe audio"""
        if not self.recording:
            return

        self.recording = False
        self.recording_status.emit(False)

        if self.recording_thread:
            self.recording_thread.join()

        # Process the recorded audio
        self._process_audio()

    def _record_audio(self):
        """Record audio in a separate thread"""
        try:
            # Try to import sounddevice here to avoid import errors
            try:
                import sounddevice as sd
                import numpy as np

                with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='int16') as stream:
                    print("Recording started...")

                    while self.recording:
                        audio_chunk, overflowed = stream.read(self.sample_rate // 10)  # 100ms chunks
                        if overflowed:
                            print("Audio buffer overflowed")

                        audio_chunk = (audio_chunk * 32767).astype(np.int16)
                        self.audio_frames.append(audio_chunk.tobytes())

                    print("Recording stopped.")
            except ImportError:
                import pyaudio

                CHUNK = 1024
                FORMAT = pyaudio.paInt16
                CHANNELS = 1
                RATE = 16000

                p = pyaudio.PyAudio()
                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)

                print("Recording started...")

                while self.recording:
                    data = stream.read(CHUNK)
                    self.audio_frames.append(data)

                stream.stop_stream()
                stream.close()
                p.terminate()
                print("Recording stopped.")

        except Exception as e:
            self.recording = False
            self.error_occurred.emit(f"Error during recording: {str(e)}")
            print(f"Error during recording: {e}")

    def _process_audio(self):
        """Process recorded audio and transcribe using Whisper API"""
        if not self.audio_frames:
            self.error_occurred.emit("No audio recorded")
            return

        if not self.client:
            self.error_occurred.emit("OpenAI client not initialized")
            return

        try:
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name

                # Write audio data to WAV file
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit audio
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_frames))

                # Transcribe using Whisper API with new client format
                with open(temp_filename, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=self.language
                    )

                # Extract transcribed text
                if transcript and hasattr(transcript, 'text'):
                    transcribed_text = transcript.text.strip()
                    print(f"Transcribed: {transcribed_text}")
                    self.transcription_complete.emit(transcribed_text)
                else:
                    self.error_occurred.emit("Failed to transcribe audio")

            try:
                os.unlink(temp_filename)
            except:
                pass

        except Exception as e:
            self.error_occurred.emit(f"Error processing audio: {str(e)}")
            print(f"Error processing audio: {e}")
