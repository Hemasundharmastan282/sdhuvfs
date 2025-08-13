import threading
import json
import websocket
from urllib.parse import urlencode
from queue import Queue
import time
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

class AssemblyAIStreamer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws = None
        self.listening = False
        self.error = None
        self._transcript_queue = Queue()
        self._audio_thread = None
        self._ws_thread = None
        self.webrtc_ctx = None

        self.SAMPLE_RATE = 16000

    def _on_open(self, ws):
        """Called when the WebSocket connection is established."""
        print("WebSocket connection opened.")
        self.listening = True
        
        def stream_audio():
            print("Starting audio streaming...")
            while self.listening:
                try:
                    frames = self.webrtc_ctx.audio_receiver.get_queued_frames()
                    if not frames:
                        time.sleep(0.01)
                        continue

                    for frame in frames:
                        try:
                            audio_segment = AudioSegment(frame.to_bytes(), sample_width=frame.sample_width, frame_rate=frame.sample_rate, channels=frame.channels)
                            audio_segment = audio_segment.set_frame_rate(self.SAMPLE_RATE).set_channels(1)
                            ws.send(audio_segment.raw_data, websocket.ABNF.OPCODE_BINARY)
                        except CouldntDecodeError:
                            continue
                except Exception as e:
                    print(f"Error streaming audio: {e}")
                    self.listening = False
                    break
            print("Audio streaming stopped.")
        
        self._audio_thread = threading.Thread(target=stream_audio)
        self._audio_thread.daemon = True
        self._audio_thread.start()

    def _on_message(self, ws, message):
        """Called when a new message is received from the WebSocket."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            if msg_type == "FinalTranscript":
                transcript = data.get('text', '')
                if transcript:
                    self._transcript_queue.put(transcript)
        except json.JSONDecodeError as e:
            print(f"Error decoding message: {e}")

    def _on_error(self, ws, error):
        """Called when a WebSocket error occurs."""
        print(f"WebSocket Error: {error}")
        self.error = str(error)
        self.listening = False

    def _on_close(self, ws, close_status_code, close_msg):
        """Called when the WebSocket connection is closed."""
        print(f"WebSocket Disconnected: Status={close_status_code}, Msg={close_msg}")
        self.listening = False

    def start(self, webrtc_ctx):
        """Connects to the API and starts sending and receiving data."""
        if self.listening:
            return

        self.webrtc_ctx = webrtc_ctx

        connection_params = {"sample_rate": self.SAMPLE_RATE, "format_turns": True}
        api_endpoint_url = "wss://streaming.assemblyai.com/v3/ws"
        api_endpoint = f"{api_endpoint_url}?{urlencode(connection_params)}"

        self.ws = websocket.WebSocketApp(
            api_endpoint,
            header={"Authorization": self.api_key},
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._ws_thread = threading.Thread(target=self.ws.run_forever)
        self._ws_thread.daemon = True
        self._ws_thread.start()

    def stop(self):
        """Stops all streaming and closes connections."""
        self.listening = False
        if self.ws:
            self.ws.close()
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=1.0)
        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=1.0)
        print("Streamer stopped.")

    def get_latest_transcript(self):
        """
        Retrieves the latest transcript from the queue without blocking.
        Returns None if the queue is empty.
        """
        if self._transcript_queue.empty():
            return None
        return self._transcript_queue.get()
