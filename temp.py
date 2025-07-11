import pycozmo
import time
import requests
import subprocess
from PIL import Image
import numpy as np
import os
from TTS.api import TTS


class CozmoEasy:
    def __init__(self):
        self.cli = pycozmo.Client()
        self.cli.start()
        time.sleep(2)
        self.cli.connect()
        self.cli.anim_controller.enabled = True
        self.cli.enable_animations()
        self.cli.load_anims()
        print("✅ Cozmo connected and animations loaded!")
        self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
        self._action_delay = 1.2

    def _wait(self, t=None):
        time.sleep(t or self._action_delay)

    def bye(self):
        self.cli.disconnect()
        self.cli.stop()
        print("🛑 Cozmo disconnected and stopped.")
        self._wait(2)

    def go(self):
        print("🚗 Moving forward")
        self.cli.drive_wheels(75, 75, duration=2.0)
        self._wait(1)

    def back(self):
        print("🔙 Moving backward")
        self.cli.drive_wheels(-75, -75, duration=2.0)
        self._wait(1)

    def left(self):
        print("↩️ Turning left")
        self.cli.drive_wheels(-50, 50, duration=1.5)
        self._wait(1)

    def right(self):
        print("↪️ Turning right")
        self.cli.drive_wheels(50, -50, duration=1.5)
        self._wait(1)

    def turn(self):
        print("↪️ Turning right")
        self.cli.drive_wheels(50, -50, duration=2.9)
        self._wait(1)

    def light_on(self):
        print("💡 Backpack lights ON")
        self.cli.set_backpack_lights(
            pycozmo.lights.green_light,
            pycozmo.lights.green_light,
            pycozmo.lights.green_light,
            pycozmo.lights.green_light,
            pycozmo.lights.green_light
        )
        self._wait(1)

    def light_off(self):
        print("❌ Backpack lights OFF")
        self.cli.set_backpack_lights(
            pycozmo.lights.off_light,
            pycozmo.lights.off_light,
            pycozmo.lights.off_light,
            pycozmo.lights.off_light,
            pycozmo.lights.off_light
        )
        self._wait(1)

    def celebrate(self):
        print("🎉 Celebrating")
        self.cli.play_anim(name="anim_greeting_happy_03")
        self._wait(8)

    def say(self, text):
        print(f"[CozmoEasy] 🗣️ Generating TTS offline for: '{text}'")
        raw_wav_path = "temp_raw.wav"
        final_wav_path = "output.wav"
        silence_path = "silence.wav"
        padded_wav_path = "padded_output.wav"

        try:
            # Step 1: Generate speech (TTS)
            self.tts.tts_to_file(text=text, file_path=raw_wav_path)

            # Step 2: Convert to Cozmo format
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_wav_path,
                "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
                final_wav_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Step 3: Generate silence
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                "-t", "1.0", "-q:a", "9", "-acodec", "pcm_s16le", silence_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Step 4: Concatenate silence + speech robustly
            subprocess.run([
                "ffmpeg", "-y",
                "-i", silence_path,
                "-i", final_wav_path,
                "-filter_complex", "[0][1]concat=n=2:v=0:a=1[a]",
                "-map", "[a]",
                padded_wav_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Step 5: Play it!
            print(f"🔊 Playing {padded_wav_path} on Cozmo...")
            self.cli.set_volume(50000)
            self.cli.play_audio(padded_wav_path)
            self.cli.wait_for(pycozmo.event.EvtAudioCompleted)

        except Exception as e:
            print("❌ Error in say():", e)
        finally:
            for f in [raw_wav_path, final_wav_path, silence_path, padded_wav_path]:
                if os.path.exists(f): os.remove(f)
            print("🧹 Cleaned up temporary files")

        self._wait(1)

    def head_up(self):
        print("⬆️ Head up")
        angle = (pycozmo.robot.MAX_HEAD_ANGLE.radians - pycozmo.robot.MIN_HEAD_ANGLE.radians) / 2.0
        self.cli.set_head_angle(angle)
        self._wait(1)

    def head_down(self):
        print("⬇️ Head down")
        self.cli.set_head_angle(pycozmo.MIN_HEAD_ANGLE.radians)
        self._wait(1)

    def hand_up(self):
        print("✋ Hand up")
        self.cli.set_lift_height(pycozmo.MAX_LIFT_HEIGHT.mm)
        self._wait(1)

    def hand_down(self):
        print("🤚 Hand down")
        self.cli.set_lift_height(pycozmo.MIN_LIFT_HEIGHT.mm)
        self._wait(1)

    def _show_emotion(self, emotion, hold=5.0):
        self.head_up()
        rate = pycozmo.robot.FRAME_RATE  # usually 30
        timer = pycozmo.util.FPSTimer(rate)
        base_face = pycozmo.expressions.Neutral()

        # Animate transition to emotion
        face_generator = pycozmo.procedural_face.interpolate(base_face, emotion, rate // 3)
        for face in face_generator:
            im = face.render()
            np_im = np.array(im)
            np_im2 = np_im[::2]
            im2 = Image.fromarray(np_im2)
            self.cli.display_image(im2)
            timer.sleep()

        # HOLD the emotion on Cozmo's face for 'hold' seconds
        emotion_image = emotion.render()
        np_emotion_image = np.array(emotion_image)[::2]
        im_emotion = Image.fromarray(np_emotion_image)
        for _ in range(int(rate * hold)):
            self.cli.display_image(im_emotion)
            timer.sleep()

        # Animate transition back to neutral (optional)
        face_generator = pycozmo.procedural_face.interpolate(emotion, base_face, rate // 3)
        for face in face_generator:
            im = face.render()
            np_im = np.array(im)
            np_im2 = np_im[::2]
            im2 = Image.fromarray(np_im2)
            self.cli.display_image(im2)
            timer.sleep()

    def angry(self):
        print("😠 Showing Anger")
        self._show_emotion(pycozmo.expressions.Anger())
        self._wait(1)

    def sad(self):
        print("😢 Showing Sadness")
        self._show_emotion(pycozmo.expressions.Sadness())
        self._wait(1)

    def happy(self):
        print("😃 Showing Happiness")
        self._show_emotion(pycozmo.expressions.Happiness())
        self._wait(1)

    def surprised(self):
        print("😮 Showing Surprise")
        self._show_emotion(pycozmo.expressions.Surprise())
        self._wait(1)

    def disgusted(self):
        print("🤢 Showing Disgust")
        self._show_emotion(pycozmo.expressions.Disgust())
        self._wait(1)

    def afraid(self):
        print(" Showing Fear")
        self._show_emotion(pycozmo.expressions.Fear())
        self._wait(1)

    def guilty(self):
        print(" Showing Guilt")
        self._show_emotion(pycozmo.expressions.Guilt())
        self._wait(1)

    def disappointed(self):
        print(" Showing Disappointment")
        self._show_emotion(pycozmo.expressions.Disappointment())
        self._wait(1)

    def embarrassed(self):
        print(" Showing Embarrassment")
        self._show_emotion(pycozmo.expressions.Embarrassment())
        self._wait(1)

    def annoyed(self):
        print(" Showing Annoyance")
        self._show_emotion(pycozmo.expressions.Annoyance())
        self._wait(1)

    def tired(self):
        print(" Showing Tiredness")
        self._show_emotion(pycozmo.expressions.Tiredness())
        self._wait(1)

    def excited(self):
        print(" Showing Excitement")
        self._show_emotion(pycozmo.expressions.Excitement())
        self._wait(1)

    def amazed(self):
        print(" Showing Amazement")
        self._show_emotion(pycozmo.expressions.Amazement())
        self._wait(1)

    def confused(self):
        print(" Showing Confusion")
        self._show_emotion(pycozmo.expressions.Confusion())
        self._wait(1)

    def bored(self):
        print(" Showing Boredom")
        self._show_emotion(pycozmo.expressions.Boredom())
        self._wait(1)

    def furious(self):
        print(" Showing Fury")
        self._show_emotion(pycozmo.expressions.Fury())
        self._wait(1)

    def suspicious(self):
        print(" Showing Suspicion")
        self._show_emotion(pycozmo.expressions.Suspicion())
        self._wait(1)

    def rejected(self):
        print(" Showing Rejection")
        self._show_emotion(pycozmo.expressions.Rejection())
        self._wait(1)

'''
    def say(self, text):
        print(f"[CozmoEasy] 🗣️ Generating TTS for: '{text}'")
        mp3_path = "output.mp3"
        wav_path = "output.wav"
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.75
                }
            }
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                raise Exception(f"ElevenLabs API error: {response.status_code} {response.text}")

            with open(mp3_path, "wb") as f:
                f.write(response.content)

            # Convert MP3 to WAV
            print("Converting MP3 to WAV...")
            command = [
                "ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", "-sample_fmt", "s16", wav_path
            ]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Play on Cozmo
            print("🔊 Playing on Cozmo")
            self.cli.set_volume(50000)
            self.cli.play_audio(wav_path)
            self.cli.wait_for(pycozmo.event.EvtAudioCompleted)
        except Exception as e:
            print("❌ Error in say_word:", e)
        finally:
            if os.path.exists(mp3_path): os.remove(mp3_path)
            if os.path.exists(wav_path): os.remove(wav_path)
            print("🧹 Cleaned up temporary files")
        self._wait(2)
        
        
        
    def say(self, text):
        print(f"[CozmoEasy] 🗣️ Generating TTS offline for: '{text}'")
        raw_wav_path = "temp_raw.wav"
        final_wav_path = "output.wav"

        try:
            # Step 1: Generate WAV using Coqui TTS
            print("📦 Generating speech using Coqui TTS...")
            #tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
            self.tts.tts_to_file(text=text, file_path=raw_wav_path)

            #tts.tts_to_file(text=text, file_path=raw_wav_path)
            print("📁 TTS saved to:", raw_wav_path)

            # Step 2: Convert to Cozmo-compatible WAV (22050 Hz, mono, s16)
            print("🔁 Converting to Cozmo-compatible WAV...")
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_wav_path,
                "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
                final_wav_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            # Step 3: Play on Cozmo
            print("🔊 Playing on Cozmo...")
            self.cli.set_volume(50000)
            self.cli.play_audio(final_wav_path)
            self.cli.wait_for(pycozmo.event.EvtAudioCompleted)

        except Exception as e:
            print("❌ Error in say():", e)

        finally:
            if os.path.exists(raw_wav_path): os.remove(raw_wav_path)
            if os.path.exists(final_wav_path): os.remove(final_wav_path)
            print("🧹 Cleaned up temporary files")

        self._wait(2)
        
    def _show_emotion(self, emotion, hold=10.0):
        self.head_up()
        rate = pycozmo.robot.FRAME_RATE
        timer = pycozmo.util.FPSTimer(rate)
        base_face = pycozmo.expressions.Neutral()

        for from_face, to_face in ((base_face, emotion), (emotion, base_face)):
            face_generator = pycozmo.procedural_face.interpolate(from_face, to_face, rate // 3)
            for face in face_generator:
                im = face.render()
                np_im = np.array(im)
                np_im2 = np_im[::2]
                im2 = Image.fromarray(np_im2)
                self.cli.display_image(im2)
                timer.sleep()

            # Hold emotion or neutral for `hold` seconds
            for _ in range(int(rate * hold)):
                timer.sleep()
'''
#ELEVENLABS_API_KEY = ""
#VOICE_ID = ""
