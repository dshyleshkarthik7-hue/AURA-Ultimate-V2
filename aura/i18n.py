import random

LANGUAGES = {
"en": "English",
"hi": "Hindi",
"te": "Telugu",
"ta": "Tamil",
"gu": "Gujarati",
}

TRANSLATIONS = {
"en": {
"steel_glass": "Steel Glass",
"steel_water_bottle": "Steel Water Bottle",
"bottle_gourd": "Bottle Gourd",
"identified": "Object Identified",
"offline": "Running Offline",
"scan_again": "Scan Again",
"scanning": "Scanning",
},

"hi": {
    "steel_glass": "स्टील का गिलास",
    "steel_water_bottle": "स्टील पानी की बोतल",
    "bottle_gourd": "लौकी",
    "identified": "वस्तु पहचान ली गई",
    "offline": "ऑफलाइन चल रहा है",
    "scan_again": "फिर से स्कैन करें",
    "scanning": "स्कैन हो रहा है",
},

"te": {
    "steel_glass": "స్టీల్ గ్లాస్",
    "steel_water_bottle": "స్టీల్ నీటి సీసా",
    "bottle_gourd": "సొరకాయ",
    "identified": "వస్తువు గుర్తించబడింది",
    "offline": "ఆఫ్‌లైన్‌లో పనిచేస్తోంది",
    "scan_again": "మళ్లీ స్కాన్ చేయండి",
    "scanning": "స్కాన్ చేస్తోంది",
},

"ta": {
    "steel_glass": "எஃகு கண்ணாடி",
    "steel_water_bottle": "எஃகு தண்ணீர் பாட்டில்",
    "bottle_gourd": "சுரைக்காய்",
    "identified": "பொருள் அடையாளம் காணப்பட்டது",
    "offline": "ஆஃப்லைனில் இயங்குகிறது",
    "scan_again": "மீண்டும் ஸ்கேன் செய்யவும்",
    "scanning": "ஸ்கேன் செய்கிறது",
},

"gu": {
    "steel_glass": "સ્ટીલનો ગ્લાસ",
    "steel_water_bottle": "સ્ટીલ પાણીની બોટલ",
    "bottle_gourd": "દૂધી",
    "identified": "વસ્તુ ઓળખાઈ ગઈ",
    "offline": "ઑફલાઇન કાર્યરત",
    "scan_again": "ફરી સ્કેન કરો",
    "scanning": "સ્કેન થઈ રહ્યું છે",
},

}

VOICE_PHRASES = {
"en": {
"steel_glass": [
"I can see a steel glass.",
"This is a steel glass.",
],
"steel_water_bottle": [
"I can see a steel water bottle.",
"This is a steel water bottle.",
],
"bottle_gourd": [
"I can see a bottle gourd.",
"This is a bottle gourd.",
],
},

"hi": {
    "steel_glass": [
        "मुझे एक स्टील का गिलास दिखाई दे रहा है।",
    ],
    "steel_water_bottle": [
        "मुझे एक स्टील पानी की बोतल दिखाई दे रही है।",
    ],
    "bottle_gourd": [
        "मुझे एक लौकी दिखाई दे रही है।",
    ],
},

"te": {
    "steel_glass": [
        "నాకు ఒక స్టీల్ గ్లాస్ కనిపిస్తోంది.",
    ],
    "steel_water_bottle": [
        "నాకు ఒక స్టీల్ నీటి సీసా కనిపిస్తోంది.",
    ],
    "bottle_gourd": [
        "నాకు ఒక సొరకాయ కనిపిస్తోంది.",
    ],
},

"ta": {
    "steel_glass": [
        "எனக்கு ஒரு எஃகு கண்ணாடி தெரிகிறது.",
    ],
    "steel_water_bottle": [
        "எனக்கு ஒரு எஃகு தண்ணீர் பாட்டில் தெரிகிறது.",
    ],
    "bottle_gourd": [
        "எனக்கு ஒரு சுரைக்காய் தெரிகிறது.",
    ],
},

"gu": {
    "steel_glass": [
        "મને એક સ્ટીલનો ગ્લાસ દેખાઈ રહ્યો છે.",
    ],
    "steel_water_bottle": [
        "મને એક સ્ટીલ પાણીની બોટલ દેખાઈ રહી છે.",
    ],
    "bottle_gourd": [
        "મને એક દૂધી દેખાઈ રહી છે.",
    ],
},

}

def get_text(key, language="en"):
    if language not in TRANSLATIONS:
        language = "en"

    if key in TRANSLATIONS[language]:
        return TRANSLATIONS[language][key]

    if key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]

    return key


def get_object_name(label, language="en"):
    return get_text(label, language)


def object_name(label, language="en"):
    return get_object_name(label, language)


def get_voice_phrase(label, language="en"):
    if language not in VOICE_PHRASES:
        language = "en"

    phrases = VOICE_PHRASES[language].get(label)

    if phrases:
        return random.choice(phrases)

    return get_object_name(label, language)
