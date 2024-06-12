import telegram
from telegram.ext import Updater, MessageHandler, Filters
import numpy as np
import cv2
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions, ResNet50
from tensorflow.keras.preprocessing import image
from PIL import Image
import speech_recognition as sr
from gtts import gTTS
import os
from pydub import AudioSegment

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
updater = Updater(token='7240624262:AAGVGFtykNFY84PaT-xOA9LvqSFmmChHjiE', use_context=True)
dispatcher = updater.dispatcher

# Load pre-trained ResNet50 model
model = ResNet50(weights='imagenet')

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="مرحباً بك في البوت!")

def handle_message(update, context):
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        process_message(update, context)
    elif 'معاذ' in update.message.text:
        process_message(update, context)

def process_message(update, context):
    if update.message.text:
        context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    elif update.message.photo:
        reply_image(update, context)
    elif update.message.voice:
        reply_voice(update, context)

def reply_image(update, context):
    # Get image file id
    file_id = update.message.photo[-1].file_id
    # Get image file
    image_file = context.bot.get_file(file_id)
    # Download image
    image_file.download('image.jpg')

    # Load and preprocess the image
    img = image.load_img('image.jpg', target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    # Use the model to predict the image
    preds = model.predict(img_array)
    # Decode predictions
    predictions = decode_predictions(preds, top=3)[0]

    # Send the predictions as a message
    message = "Predictions:\n"
    for pred in predictions:
        message += f"{pred[1]}: {pred[2]}\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def reply_voice(update, context):
    # Get voice file id
    file_id = update.message.voice.file_id
    # Get voice file
    voice_file = context.bot.get_file(file_id)
    # Download voice file
    voice_file.download('voice.ogg')

    # Convert OGG file to WAV
    audio = AudioSegment.from_ogg('voice.ogg')
    audio.export('voice.wav', format='wav')

    # Recognize speech using SpeechRecognition
    recognizer = sr.Recognizer()
    with sr.AudioFile('voice.wav') as source:
        audio_data = recognizer.record(source)
        try:
            # Try recognizing Arabic (Palestinian)
            text = recognizer.recognize_google(audio_data, language="ar-PS")
            tts = gTTS(text=text, lang='ar')
            tts.save("response_ar.mp3")
            audio_response = AudioSegment.from_mp3("response_ar.mp3")
            audio_response.export("response.ogg", format="ogg")
            context.bot.send_voice(chat_id=update.effective_chat.id, voice=open("response.ogg", 'rb'))
        except sr.UnknownValueError:
            try:
                # Try recognizing Spanish
                text = recognizer.recognize_google(audio_data, language="es-ES")
                tts = gTTS(text=text, lang='es')
                tts.save("response_es.mp3")
                audio_response = AudioSegment.from_mp3("response_es.mp3")
                audio_response.export("response.ogg", format="ogg")
                context.bot.send_voice(chat_id=update.effective_chat.id, voice=open("response.ogg", 'rb'))
            except sr.UnknownValueError:
                context.bot.send_message(chat_id=update.effective_chat.id, text="لم أستطع فهم الصوت المرسل. حاول مرة أخرى.")
        except sr.RequestError as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"تعذر طلب النتائج من خدمة التعرف على الصوت من ؛ {e}")

start_handler = MessageHandler(Filters.command, start)
message_handler = MessageHandler(Filters.all, handle_message)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(message_handler)

updater.start_polling()
updater.idle()
