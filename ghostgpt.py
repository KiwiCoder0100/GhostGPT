import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog, ttk
import speech_recognition as sr
import azure.cognitiveservices.speech as speechsdk
import openai
import os
import webbrowser
import xml.etree.ElementTree as ET
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
from azure.core.credentials import AzureKeyCredential


def open_github_link(event):
    webbrowser.open("https://github.com/ghostkiwicoder")


def create_and_open_api_key_file():
    api_key_file = "apikey.xml"
    if not os.path.isfile(api_key_file):
        root = ET.Element("config")
        ET.SubElement(root, "azure_api_key").text = "your-azure-api-key"
        ET.SubElement(root, "azure_region").text = "your-azure-region"
        ET.SubElement(root, "openai_api_key").text = "your-openai-api-key"  # Add this line

        tree = ET.ElementTree(root)
        tree.write(api_key_file)

    os.startfile(api_key_file)
    check_api_key_file()


def check_api_key_file():
    api_key_file = "apikey.xml"
    if not os.path.isfile(api_key_file):
        api_key_status.config(text="Please load your API key", fg="red")
    else:
        tree = ET.parse(api_key_file)
        root = tree.getroot()

        azure_api_key = root.find("azure_api_key").text.strip() if root.find("azure_api_key") is not None else ""
        azure_region = root.find("azure_region").text.strip() if root.find("azure_region") is not None else ""
        openai_api_key = root.find("openai_api_key").text.strip() if root.find("openai_api_key") is not None else ""

        if (azure_api_key and azure_api_key != "your-azure-api-key" and
                azure_region and azure_region != "your-azure-region" and
                openai_api_key and openai_api_key != "your-openai-api-key"):
            api_key_status.config(text="API Key Ready", fg="green")
            load_voices(azure_api_key, azure_region)
            openai.api_key = openai_api_key
        else:
            api_key_status.config(text="Please load your API key", fg="red")




def export_chat():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(chat_log.get(1.0, "end"))


def talk_to_gpt(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()


def send_message():
    message = entry.get()
    if not message:
        return
    chat_log.config(state="normal")
    chat_log.insert("end", f"User: {message}\n")
    chat_log.tag_configure("user", foreground="white")
    chat_log.tag_add("user", chat_log.index("end - 2 lines linestart"), chat_log.index("end - 2 lines lineend"))
    chat_log.see("end")
    entry.delete(0, "end")
    response = talk_to_gpt(message)
    chat_log.insert("end", f"GhostGPT: {response}\n")
    chat_log.tag_configure("gpt", foreground="cyan")
    chat_log.tag_add("gpt", chat_log.index("end - 2 lines linestart"), chat_log.index("end - 2 lines lineend"))
    chat_log.see("end")
    chat_log.config(state="disabled")
    print(response)
    speak(response)


def listen_to_user():
    start_button.config(text="Listening...")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
    try:
        user_text = recognizer.recognize_google(audio)
        entry.delete(0, "end")
        entry.insert(0, user_text)
        send_message()
    except sr.UnknownValueError:
        entry.delete(0, "end")
        entry.insert(0, "Voice not recognized.")
    start_button.config(text="Start Talking")


def clear_chat():
    chat_log.config(state="normal")
    chat_log.delete(1.0, "end")
    chat_log.config(state="disabled")


def speak(text):
    tree = ET.parse("apikey.xml")
    root = tree.getroot()

    azure_api_key = root.find("azure_api_key").text.strip()
    azure_region = root.find("azure_region").text.strip()

    speech_config = SpeechConfig(subscription=azure_api_key, region=azure_region)
    speech_config.speech_synthesis_voice_name = voice_combobox.get()

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    synthesizer.speak_text_async(text).get()



def load_voices(api_key, region):
    speech_config = SpeechConfig(subscription=api_key, region=region)
    synthesizer = SpeechSynthesizer(speech_config=speech_config)

    voices_result = synthesizer.get_voices_async().get()
    voice_names = [voice.name for voice in voices_result.voices]

    voice_combobox["values"] = voice_names
    voice_combobox.current(0)


root = tk.Tk()
root.title("GhostGPT")
root.configure(bg="black")

chat_log = ScrolledText(root, wrap="word", width=50, height=20, bg="black", fg="white", state="disabled")
chat_log.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

entry = tk.Entry(root, width=40, bg="black", fg="white")
entry.grid(row=1, column=0, padx=5, pady=5)

export_button = tk.Button(root, text="Export Chat", command=export_chat, bg="black", fg="white", width=10)
export_button.grid(row=3, column=0, padx=5, pady=5)

voice_combobox = ttk.Combobox(root, width=90)
voice_combobox.grid(row=7, column=0, padx=5, pady=5)

send_button = tk.Button(root, text="Send", command=send_message, bg="black", fg="white", width=10)
send_button.grid(row=1, column=1, padx=5, pady=5)

start_button = tk.Button(root, text="Start Talking", command=listen_to_user, bg="black", fg="white", width=10)
start_button.grid(row=2, column=0, padx=5, pady=5)

clear_button = tk.Button(root, text="Clear", command=clear_chat, bg="black", fg="white", width=10)
clear_button.grid(row=2, column=1, padx=5, pady=5)

api_key_button = tk.Button(root, text="API Key", command=create_and_open_api_key_file, bg="black", fg="white", width=10)
api_key_button.grid(row=3, column=1, padx=5, pady=5)

refresh_button = tk.Button(root, text="Refresh Voices", command=lambda: check_api_key_file(), bg="black", fg="white", width=12)
refresh_button.grid(row=4, column=1, padx=5, pady=5)

api_key_status = tk.Label(root, text="", bg="black")
api_key_status.grid(row=4, column=0, padx=5, pady=5)

version_label = tk.Label(root, text="GhostGPT by Ghost v.1.0.0", fg="red", bg="black", font=("Helvetica", 13, "italic"))
version_label.grid(row=5, column=0, padx=5, pady=0)

github_link = tk.Label(root, text="github.com/ghostkiwicoder", fg="cyan", cursor="hand2", bg="black", font=("Helvetica", 11, "italic"))
github_link.grid(row=6, column=0, padx=5, pady=0)
github_link.bind("<Button-1>", open_github_link)

check_api_key_file()

root.mainloop()


