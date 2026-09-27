import threading
import time

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

class Voice:

    def __init__(self, enabled=True, cooldown=4):
        self.enabled = enabled
        self.cooldown = float(cooldown)
        self.last_time = 0.0
        self.engine = None
        self.lock = threading.Lock()

        if self.enabled and pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 155)
                self.engine.setProperty("volume", 1.0)
                print("Voice engine started successfully.")
            except Exception as error:
                print("Voice initialization error:", error)
                self.engine = None

    def get_text(self, label, language):

        texts = {
        "en": {
            "steel_glass": "Hello! I found a steel glass.",
            "steel_water_bottle": "Hello! I found a steel water bottle.",
            "bottle_gourd": "Hello! I found a bottle gourd."
        },

        "hi": {
            "steel_glass": "नमस्ते! मुझे एक स्टील का गिलास दिखाई दे रहा है।",
            "steel_water_bottle": "नमस्ते! मुझे एक स्टील पानी की बोतल दिखाई दे रही है।",
            "bottle_gourd": "नमस्ते! मुझे एक लौकी दिखाई दे रही है।"
        },

        "te": {
            "steel_glass": "హలో! నాకు ఒక స్టీల్ గ్లాస్ కనిపిస్తోంది.",
            "steel_water_bottle": "హలో! నాకు ఒక స్టీల్ నీళ్ల బాటిల్ కనిపిస్తోంది.",
            "bottle_gourd": "హలో! నాకు ఒక సొరకాయ కనిపిస్తోంది."
        },

        "ta": {
            "steel_glass": "வணக்கம்! எனக்கு ஒரு எஃகு கண்ணாடி தெரிகிறது.",
            "steel_water_bottle": "வணக்கம்! எனக்கு ஒரு எஃகு தண்ணீர் பாட்டில் தெரிகிறது.",
            "bottle_gourd": "வணக்கம்! எனக்கு ஒரு சுரைக்காய் தெரிகிறது."
        },

        "gu": {
            "steel_glass": "નમસ્તે! મને એક સ્ટીલનો ગ્લાસ દેખાઈ રહ્યો છે.",
            "steel_water_bottle": "નમસ્તે! મને એક સ્ટીલ પાણીની બોટલ દેખાઈ રહી છે.",
            "bottle_gourd": "નમસ્તે! મને એક દૂધી દેખાઈ રહી છે."
        }
    }

        if language not in texts:
            language = "en"

        if label in texts[language]:
            return texts[language][label]

        return "Object identified."

    def find_voice(self, language):

        if self.engine is None:
            return None

        keywords = {
        "en": ["english", "zira", "david"],
        "hi": ["hindi", "hi-in"],
        "te": ["telugu", "te-in"],
        "ta": ["tamil", "ta-in"],
        "gu": ["gujarati", "gu-in"]
    }

        search_words = keywords.get(language, keywords["en"])

        try:
            voices = self.engine.getProperty("voices")

            for voice in voices:

                voice_info = (
                    str(getattr(voice, "name", "")) + " "
                    + str(getattr(voice, "id", "")) + " "
                    + str(getattr(voice, "languages", ""))
                ).lower()

                for word in search_words:
                    if word.lower() in voice_info:
                        return voice.id

        except Exception as error:
            print("Voice search error:", error)

        return None

    def speak(self, text, language):

        if self.engine is None:
            return

        try:
            with self.lock:

                voice_id = self.find_voice(language)

                if voice_id is not None:
                    self.engine.setProperty("voice", voice_id)
                else:
                    print("No local voice found for:", language)

                self.engine.say(text)
                self.engine.runAndWait()

        except Exception as error:
            print("Voice error:", error)

    def announce(self, label, language="en"):

        if not self.enabled:
            return

        if self.engine is None:
            print("Voice engine is unavailable.")
            return

        current_time = time.time()

        if current_time - self.last_time < self.cooldown:
            return

        self.last_time = current_time

        text = self.get_text(label, language)

        print("Speaking:", text)

        voice_thread = threading.Thread(
            target=self.speak,
            args=(text, language),
            daemon=True
        )

        voice_thread.start()

    def close(self):

        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass