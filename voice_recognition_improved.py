"""
Improved voice recognition module using OpenAI's Whisper API.
This version includes better audio recording, error handling, and debugging.
"""

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
    audio_level = pyqtSignal(float)  # New signal for audio level monitoring
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.audio_frames = []
        self.sample_rate = 16000  # 16kHz is optimal for Whisper
        self.channels = 1  # Mono audio
        self.recording_thread = None
        self.language = "en"  # Default language is English
        self.debug_mode = True  # Set to True to save debug audio files
        
        # Initialize OpenAI client
        self.client = None
        try:
            with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
                api_key = file.read().strip()
                self.client = OpenAI(api_key=api_key)
                print("Voice recognizer OpenAI client initialized successfully")
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
            self.recording_thread.join(timeout=2.0)  # Add timeout to prevent hanging
            
        # Process the recorded audio
        self._process_audio()
    
    def _record_audio(self):
        """Record audio in a separate thread with improved quality"""
        try:
            # Try to import sounddevice here to avoid import errors
            try:
                import sounddevice as sd
                import numpy as np
                
                # Higher quality recording settings
                with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, 
                                   dtype='float32', blocksize=1024, latency='low') as stream:
                    print("Recording started with sounddevice...")
                    
                    while self.recording:
                        audio_chunk, overflowed = stream.read(1024)
                        if overflowed:
                            print("Audio buffer overflowed")
                        
                        # Calculate audio level for visualization
                        if len(audio_chunk) > 0:
                            audio_level = float(np.abs(audio_chunk).mean())
                            self.audio_level.emit(audio_level * 100)  # Scale for better visualization
                        
                        # Convert to int16 and append to frames
                        audio_chunk = (audio_chunk * 32767).astype(np.int16)
                        self.audio_frames.append(audio_chunk.tobytes())
                        
                    print("Recording stopped.")
            except ImportError:
                # Fallback to pyaudio if sounddevice is not available
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
                
                print("Recording started with pyaudio...")
                
                while self.recording:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    
                    # Calculate audio level for visualization (simplified for pyaudio)
                    try:
                        import numpy as np
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        audio_level = float(np.abs(audio_data).mean()) / 32767.0
                        self.audio_level.emit(audio_level * 100)
                    except ImportError:
                        pass  # Skip audio level if numpy is not available
                
                stream.stop_stream()
                stream.close()
                p.terminate()
                print("Recording stopped.")
                
        except Exception as e:
            self.recording = False
            self.error_occurred.emit(f"Error during recording: {str(e)}")
            print(f"Error during recording: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_audio(self):
        """Process recorded audio and transcribe using Whisper API with improved error handling"""
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
                
                # Save a debug copy if debug mode is enabled
                if self.debug_mode:
                    debug_dir = os.path.join(os.path.dirname(__file__), 'debug_audio')
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = os.path.join(debug_dir, f"debug_audio_{int(time.time())}.wav")
                    with open(temp_filename, 'rb') as src, open(debug_file, 'wb') as dst:
                        dst.write(src.read())
                    print(f"Debug audio saved to: {debug_file}")
                
                # Get file size for debugging
                file_size = os.path.getsize(temp_filename) / 1024  # Size in KB
                print(f"Audio file size: {file_size:.2f} KB")
                
                # Check if file is too small (likely no audio)
                if file_size < 5:  # Less than 5KB
                    self.error_occurred.emit("Audio recording too short or no audio detected")
                    return
                
                # Transcribe using Whisper API
                try:
                    print(f"Transcribing audio with language: {self.language}")
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
                        self.error_occurred.emit("Failed to transcribe audio: No text returned")
                except Exception as api_error:
                    self.error_occurred.emit(f"Whisper API error: {str(api_error)}")
                    print(f"Whisper API error: {api_error}")
                    import traceback
                    traceback.print_exc()
                    
            # Clean up temporary file
            try:
                if not self.debug_mode:  # Keep the file if in debug mode
                    os.unlink(temp_filename)
            except Exception as e:
                print(f"Error deleting temporary file: {e}")
                
        except Exception as e:
            self.error_occurred.emit(f"Error processing audio: {str(e)}")
            print(f"Error processing audio: {e}")
            import traceback
            traceback.print_exc()
