import os
import youtube_dl
import speech_recognition as sr


def download_and_transcribe_video(video_url, output_dir):
    """
    Скачивает видео с YouTube и транскрибирует аудио.

    Args:
        video_url (str): URL видео на YouTube.
        output_dir (str): Путь к директории для сохранения файлов.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Скачиваем видео
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s')
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)

    # Транскрибируем аудио
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
    transcript = r.recognize_google(audio, language='en-US')

    # Сохраняем транскрипт
    transcript_filename = os.path.splitext(filename)[0] + '.txt'
    with open(transcript_filename, 'w', encoding='utf-8') as f:
        f.write(transcript)


# Пример использования
download_and_transcribe_video(
    video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    output_dir='transcripts/'
)
