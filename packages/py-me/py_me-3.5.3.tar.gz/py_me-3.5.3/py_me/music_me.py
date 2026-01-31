import threading
import os
import pygame
import time
import tempfile
from pydub import AudioSegment

class NoReturn:
    pass

class Auxiliary:
    def __init__(self):
        self.sound = None
        self.thread = None

# backward-compatible alias
alxiliar = Auxiliary

class music_me:
    """
    Created to play and manipulate audio for any purpose (despite the name).

    Methods:
        loop_soundtrack(speed, file)
        musical_element(speed, file, wait_time=0)
        pitched_musical_element(speed, pitch, file, wait_time=0)
        stop_element_after(element, seconds_after_start)

    """
    pygame.mixer.init()

    def loop_soundtrack(speed: int, file: str) -> Auxiliary:
        """
        Play a soundtrack in an infinite loop with optional speed change.

        Args:
            speed (int): playback speed multiplier.
            file (str): the exact file to play.

        Behavior:
            - plays a file in loop
            - may modify its speed
        Example:
            >>> from py_me import music_me
            >>> music_me.loop_soundtrack(2, "my_beat.mp3")
        Returns:
            Auxiliary: object containing pygame Sound and thread for light control
        """
        aux = Auxiliary()
        def player():
            audio = AudioSegment.from_file(file)
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            }).set_frame_rate(audio.frame_rate)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            audio.export(temp_path, format="wav")

            aux.sound = pygame.mixer.Sound(temp_path)
            aux.sound.play(loops=-1)

            print(f"Playing {file} in loop (speed {speed}x)")

            while True:
                time.sleep(0.1)

        th = threading.Thread(target=player, daemon=True)
        aux.thread = th
        th.start()
        return aux

    def musical_element(speed: int, file: str, wait_time: int =0) -> Auxiliary:
        """
        Play a musical element after an optional wait time.

        Args:
            speed (int): playback speed multiplier.
            file (str): file to play.
            wait_time (int): seconds to wait after script start before playing.

        Behavior:
            - plays a file
            - may change its speed
            - can wait a specified time before playback
        Example:
            >>> from py_me import music_me
            >>> music_me.musical_element(1, "my_sound.mp3", 21)
        Returns:
            Auxiliary: object containing pygame Sound and thread
        """
        aux = Auxiliary()
        def player():
            if wait_time > 0:
                time.sleep(wait_time)

            audio = AudioSegment.from_file(file)
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            }).set_frame_rate(audio.frame_rate)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            audio.export(temp_path, format="wav")

            aux.sound = pygame.mixer.Sound(temp_path)
            aux.sound.play()

            print(f"Playing {file} (speed {speed}x) after {wait_time}s")

            time.sleep(audio.duration_seconds)
            os.remove(temp_path)

        th = threading.Thread(target=player, daemon=True)
        aux.thread = th
        th.start()
        return aux

    def pitched_musical_element(speed: int, pitch: int, file: str, wait_time: int=0) -> Auxiliary:
        """
        Play a musical element with adjustable speed and pitch.

        Args:
            speed (int): playback speed multiplier.
            pitch (int): pitch multiplier.
            file (str): file to play.
            wait_time (int): seconds to wait before playback.

        Behavior:
            - plays a sound file
            - may change speed and/or pitch
            - starts after specified wait time
        Example:
            >>> from py_me import music_me
            >>> music_me.pitched_musical_element(1, 3, "my_sound.wav", 12)
        Returns:
            Auxiliary: object containing pygame Sound and thread
        """
        aux = Auxiliary()
        def player():
            if wait_time > 0:
                time.sleep(wait_time)

            audio = AudioSegment.from_file(file)
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed * pitch)
            }).set_frame_rate(audio.frame_rate)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            audio.export(temp_path, format="wav")

            aux.sound = pygame.mixer.Sound(temp_path)
            aux.sound.play()

            print(f"Playing {file} (speed {speed}x, pitch {pitch}x)")

            time.sleep(audio.duration_seconds)
            os.remove(temp_path)

        th = threading.Thread(target=player, daemon=True)
        aux.thread = th
        th.start()
        return aux

    def stop_element_after(element: Auxiliary, seconds_after_start: int) -> NoReturn:
        """
        Stop playback of an element after a specified number of seconds.

        Args:
            element (Auxiliary): the element to stop.
            seconds_after_start (int): seconds after start when the element should stop.

        Behavior:
            - stops the given musical element after the specified time
        Example:
            >>> from py_me import music_me
            >>> elem = music_me.musical_element(1, "sound.wav", 12)
            >>> music_me.stop_element_after(elem, 23)
        Returns:
            None
        """
        def stop() -> NoReturn:
            """stop👍"""
            try:
                if hasattr(element, "sound") and element.sound:
                    element.sound.stop()
                    print("Playback stopped automatically.")
            except Exception as e:
                print(f"Error trying to stop the element: {e}")

        threading.Timer(seconds_after_start, stop).start()

    def stop_all_after(delay_seconds: float) -> NoReturn:
        """
        Stop all currently playing sounds after a delay.

        Args:
            delay_seconds (float): seconds after program start to stop everything.

        Behavior:
            - stops all sounds after the given delay
        Example:
            >>> from py_me import music_me
            >>> music_me.loop_soundtrack(2, "beat.mp3")
            >>> music_me.musical_element(1, "element.wav", 2)
            >>> music_me.stop_all_after(20)
        Returns:
            None
        """
        def stop_all() -> NoReturn:
            """stop all 👍"""
            try:
                if pygame.mixer.get_init() and pygame.mixer.get_busy():
                    pygame.mixer.stop()
                    print("All playback stopped")
                else:
                    print("No sounds are playing")
            except Exception as e:
                print("An unexpected error occurred:")
                print(e)

        threading.Timer(delay_seconds, stop_all).start()

    def set_master_volume(volume: float, delay: float) -> NoReturn:
        """
        Set the master volume for all sounds after a delay.

        Args:
            volume (float): desired volume between 0.0 and 1.0.
            delay (float): seconds after program start to apply the volume.

        Behavior:
            - adjusts master volume after delay
        Example:
            >>> from py_me import music_me
            >>> music_me.loop_soundtrack(2, "beat.mp3")
            >>> music_me.musical_element(1, "element.wav", 2)
            >>> music_me.set_master_volume(0.5, 20)
        Returns:
            None
        """
        def adjust():
            try:
                if 0.0 <= volume <= 1.0:
                    for i in range(pygame.mixer.get_num_channels()):
                        ch = pygame.mixer.Channel(i)
                        if ch.get_busy():
                            snd = ch.get_sound()
                            if snd:
                                snd.set_volume(volume)
                    print(f"Master volume set to {volume * 100}%")
                else:
                    print("Volume must be between 0.0 and 1.0")
            except Exception as e:
                print("An unexpected error occurred:")
                print(e)

        threading.Timer(delay, adjust).start()

    def set_element_volume(element: Auxiliary, volume: float, delay: float) -> NoReturn:
        """
        Set the volume of a specific element after a delay.

        Args:
            element (Auxiliary): the element whose volume will be adjusted.
            volume (float): desired volume between 0.0 and 1.0.
            delay (float): seconds after program start to apply the volume.

        Behavior:
            - adjusts the volume of a specific element after delay
        Example:
            >>> from py_me import music_me
            >>> elem = music_me.musical_element(1, "element.wav", 2)
            >>> music_me.set_element_volume(elem, 0.3, 20)
        Returns:
            None
        """
        def adjust():
            try:
                if hasattr(element, "sound") and element.sound:
                    if 0.0 <= volume <= 1.0:
                        for i in range(pygame.mixer.get_num_channels()):
                            channel = pygame.mixer.Channel(i)
                            if channel.get_sound() == element.sound:
                                channel.set_volume(volume)
                        print(f"Element volume set to {volume * 100}%")
                    else:
                        print("Volume must be between 0.0 and 1.0")
                else:
                    print("Invalid element or not playing")
            except Exception as e:
                print("An unexpected error occurred:")
                print(e)
        threading.Timer(delay, adjust).start()