"""
Convert text to audio(mp3 format ) file with subtitles(.lrc).
for foreign language learner 
"""
import configparser
import asyncio
import os
import sys
import time
import edge_tts
import inquirer
import constants
import platform
# import gtts
# from gtts import gTTS
from pydub import AudioSegment
from util import formattime, ms2time, get_valid_filename, delete_dir
"""export directory"""


async def create_mp3(export_file_name, sentences, tts_voice) -> None:
    print("audio generating...")
    """Main function"""
    for se in sentences:
        temp_filename = str(round(time.time() * 1000))
        se['file_path'] = constants.TEMP_PATH + '/' + temp_filename + '.mp3'
        communicate = edge_tts.Communicate(se['tts'], tts_voice)
        await communicate.save(se['file_path'])
        await asyncio.sleep(1)

    audios = AudioSegment.silent(duration=1000)
    lrc_timestamp = 1000
    lrc_lines = ['[ti:text-tts-mp3lrc]\n']
    for se in sentences:
        audio_file = AudioSegment.from_mp3(se['file_path'])
        audio_file_length = int(len(audio_file))
        # tts text
        lrc_lines.append('[' + ms2time(lrc_timestamp) + ']' +
                         se['tts'].replace(constants.DELEMIER, ' ') + '\n')
        tts_timestamp = lrc_timestamp
        lrc_timestamp = lrc_timestamp + audio_file_length

        # display text
        if len(se['text'].split(constants.DELEMIER)) > 1:
            meaning_text = se['text'].replace(se['tts'], '').replace(
                constants.DELEMIER, ' ')
            meaning_texts = meaning_text.split('\\n')
            for text in meaning_texts:
                lrc_lines.append('[' + ms2time(lrc_timestamp) + ']' + text +
                                 '\n')
                text_duration = int(len(text) * 100)
                if text_duration > 2000:
                    text_duration = 2000
                lrc_timestamp = text_duration + lrc_timestamp

        silent_delay = lrc_timestamp - tts_timestamp - audio_file_length
        if silent_delay < 500:
            silent_delay = 500

        audios = audios + audio_file + AudioSegment.silent(
            duration=silent_delay)
    audios = audios + AudioSegment.silent(duration=constants.SILENT_TIME)
    export_file_path = constants.EXPORT_PATH + '/' + export_file_name + '.mp3'

    audios.export(export_file_path)

    print(export_file_path + ' created success.')

    with open(export_file_path.replace('.mp3', '.lrc'), 'w',
              encoding='utf-8') as f:
        f.writelines(lrc_lines)
        f.close()


async def select_tts_engine():

    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    voice = config['config']['voice'] if 'voice' in config['config'] else None
    voice_list = config['config']['voice_list'] if 'voice_list' in config[
        'config'] else None

    if voice_list is None:
        print('load voices list \n')
        # voice_gtts = gtts.lang.tts_langs()
        # print(voice_gtts)
        voicesManager = await edge_tts.VoicesManager.create()
        voice_list = []
        for language in voicesManager.voices:
            voice_list.append(language['ShortName'])
        config.set('config', 'voice_list', ','.join(voice_list))
    else:
        voice_list = voice_list.split(',')

    config.write(open(config_path, 'w', encoding='utf-8'))

    countries = []
    for name in voice_list:
        if not name.split('-')[0] in countries:
            countries.append(name.split('-')[0])

    result = ''

    if not (voice is None) and len(voice) > 0:
        answer = input("Use voice {0} : [y/n]".format(voice))
        if not answer or answer[0].lower() == 'y':
            return voice

    questions = [
        inquirer.List(
            'language',
            message="What language  do you choose?",
            choices=countries,
        ),
    ]

    answers = inquirer.prompt(questions)
    voices = []
    for name in voice_list:
        if name.split('-')[0] == answers['language']:
            voices.append(name)

    questions = [
        inquirer.List(
            'voice',
            message="What voice  do you choose?",
            choices=voices,
        ),
    ]

    answers = inquirer.prompt(questions)
    result = answers["voice"]
    config.set('config', 'voice', result)
    config.write(open(config_path, 'w', encoding='utf-8'))

    return result


def init():
    delete_dir(constants.TEMP_PATH)
    if not os.path.exists(constants.CONFIG_FILE):
        config = configparser.ConfigParser()
        config.read(constants.CONFIG_FILE)
        config.add_section('config')
        with open(constants.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    if not os.path.exists(constants.TEMP_PATH):
        os.makedirs(constants.TEMP_PATH)

    if not os.path.exists(constants.EXPORT_PATH):
        os.makedirs(constants.EXPORT_PATH)


async def main(loop):

    init()
    sentences = []
    tts_voice = await select_tts_engine()
    export_file_name = ''

    print(constants.TEXT_USAGE_NOTE)

    while True:

        input_tips = constants.TEXT_INPUT_CONTIUNE if len(
            sentences) > 0 else constants.TEXT_INPUT_SENTENCE
        text = input(input_tips)

        if len(text) > 0:
            tts = text
            tts = text.split(constants.DELEMIER)[0]
            sentences.append({'text': text, 'tts': tts})
            continue
        else:
            if len(sentences) == 0:
                break
        try:
            if export_file_name == '' and len(sentences) > 0:
                export_file_name = get_valid_filename(
                    sentences[0]['text'].split(constants.DELEMIER)[0])
            await create_mp3(export_file_name, sentences, tts_voice)
        finally:
            sentences = []
            export_file_name = ''


if __name__ == "__main__":

    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        loop.close()
