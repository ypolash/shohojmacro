"""
reCAPTCHA Audio Solver (Ban-Proof Implementation)
Uses Playwright to intercept the native audio stream and Google STT to transcribe it.
"""
import os
import time
import threading
from typing import Optional
from playwright.sync_api import sync_playwright

import speech_recognition as sr
from pydub import AudioSegment


class ReCaptchaSolver:
    def __init__(self, cdp_bridge):
        self.cdp_bridge = cdp_bridge
        self.audio_data = None
        self.intercept_done = threading.Event()

    def _handle_response(self, response):
        """Playwright callback to catch the mp3 stream natively from the browser."""
        if "payload/audio.mp3" in response.url:
            print(f"[reCAPTCHA] Intercepted native audio buffer from: {response.url}")
            try:
                self.audio_data = response.body()
                self.intercept_done.set()
            except Exception as e:
                print(f"[reCAPTCHA] Failed to read audio buffer: {e}")

    def solve(self, timeout_ms=30000) -> Optional[str]:
        """
        Attempts to solve an open reCAPTCHA by triggering the audio challenge,
        intercepting the audio natively, and using speech recognition.
        """
        if not self.cdp_bridge.ws_url:
            return None

        self.audio_data = None
        self.intercept_done.clear()

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self.cdp_bridge.ws_url)
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                if not valid_pages: return None
                page = valid_pages[-1]

                # 1. Start intercepting responses
                page.on("response", self._handle_response)

                # 2. Find the iframe for the active challenge
                challenge_iframe = None
                for frame in page.frames:
                    if "bframe" in frame.url or "payload" in frame.url:
                        challenge_iframe = frame
                        break
                        
                if not challenge_iframe:
                    print("[reCAPTCHA] Could not find the challenge bframe.")
                    return None

                # 3. Click the Audio button via Javascript (safest for iframes)
                try:
                    challenge_iframe.click("#recaptcha-audio-button", timeout=3000)
                    print("[reCAPTCHA] Clicked Audio button.")
                except Exception:
                    print("[reCAPTCHA] Audio button not found. Is it blocked or already on the audio page?")

                # 4. Wait for the Play button and click it to trigger the network request
                try:
                    # Give it a second to load the audio tab
                    time.sleep(1)
                    # The network request usually fires immediately when the audio tab opens,
                    # but sometimes requires clicking play.
                    play_btn = challenge_iframe.locator(".rc-audiochallenge-play-button .rc-button-default")
                    if play_btn.count() > 0:
                        play_btn.click(timeout=2000)
                except Exception as e:
                    print(f"[reCAPTCHA] Play button click failed: {e}")

                # 5. Wait for the interceptor to catch the audio buffer
                if not self.intercept_done.wait(timeout=10.0):
                    print("[reCAPTCHA] Timeout waiting for audio buffer to be intercepted.")
                    
                    # Fallback: Sometimes the audio src is directly embedded in an audio tag
                    try:
                        audio_src = challenge_iframe.locator("#audio-source").get_attribute("src", timeout=2000)
                        if audio_src:
                            print(f"[reCAPTCHA] Found audio source URL directly: {audio_src}")
                            # We can fetch it natively via page.evaluate to use the browser's fetch
                            buffer_array = page.evaluate("""async (url) => {
                                const resp = await fetch(url);
                                const buf = await resp.arrayBuffer();
                                return Array.from(new Uint8Array(buf));
                            }""", audio_src)
                            if buffer_array:
                                self.audio_data = bytes(buffer_array)
                    except Exception as e:
                        print(f"[reCAPTCHA] Fallback fetch failed: {e}")
                        
                    if not self.audio_data:
                        return None

                # 6. Save the mp3 buffer to disk temporarily
                mp3_path = "temp_recaptcha.mp3"
                wav_path = "temp_recaptcha.wav"
                
                with open(mp3_path, "wb") as f:
                    f.write(self.audio_data)

                # 7. Convert MP3 to WAV using pydub
                print("[reCAPTCHA] Converting audio...")
                # Ensure ffmpeg is in path, or set it explicitly if we downloaded it
                if os.path.exists("ffmpeg.exe"):
                    AudioSegment.converter = os.path.abspath("ffmpeg.exe")
                    
                sound = AudioSegment.from_mp3(mp3_path)
                sound.export(wav_path, format="wav")

                # 8. Use SpeechRecognition to transcribe
                print("[reCAPTCHA] Transcribing audio with Google STT...")
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio_for_stt = recognizer.record(source)

                try:
                    text = recognizer.recognize_google(audio_for_stt)
                    print(f"[reCAPTCHA] Transcription successful: '{text}'")
                except sr.UnknownValueError:
                    print("[reCAPTCHA] Google STT could not understand audio.")
                    return None
                except sr.RequestError as e:
                    print(f"[reCAPTCHA] Could not request results from STT service; {e}")
                    return None
                    
                # Clean up temp files
                try:
                    os.remove(mp3_path)
                    os.remove(wav_path)
                except:
                    pass

                # 9. Type the text into the input box and verify
                try:
                    input_box = challenge_iframe.locator("#audio-response")
                    input_box.fill(text.lower())
                    time.sleep(0.5)
                    challenge_iframe.click("#recaptcha-verify-button")
                    print("[reCAPTCHA] Solution submitted.")
                    time.sleep(1.5) # Wait to see if it was accepted
                    
                    # Verify if it was accepted by checking if the frame disappeared or shows an error
                    error_msg = challenge_iframe.locator(".rc-audiochallenge-error-message")
                    if error_msg.count() > 0 and error_msg.is_visible():
                        print("[reCAPTCHA] Solution was rejected by Google.")
                        return None
                        
                    return text.lower()
                    
                except Exception as e:
                    print(f"[reCAPTCHA] Failed to submit solution: {e}")
                    return None

            finally:
                browser.close()
