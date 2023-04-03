import librosa
import soundfile as sf


def change_voice(filename, output_filename, voice_type='orc', rate=44100):
    # Загрузка аудио файла
    audio_data, _ = librosa.load(filename, sr=rate)

    if voice_type == 'orc':
        pitch_shift = -4
        speed_factor = 1.2
    elif voice_type == 'elf':
        pitch_shift = 4
        speed_factor = 0.9
    else:
        raise ValueError(f"Unsupported voice type: {voice_type}")

    # Изменение питча
    audio_data = librosa.effects.pitch_shift(audio_data, sr=rate, n_steps=pitch_shift)

    # Изменение скорости
    audio_data = librosa.effects.pitch_shift(audio_data, sr=rate, n_steps=0, bins_per_octave=int(12 / speed_factor))

    # Добавление реверберации
    reverb_amount = 0.3
    reverb_data = librosa.effects.preemphasis(audio_data)
    audio_data = audio_data * (1 - reverb_amount) + reverb_data * reverb_amount

    # Сохранение обработанного аудио в файл
    sf.write(output_filename, audio_data, rate, subtype='PCM_16')


def main():
    input_filename = 'input.wav'
    output_filename_orc = 'output_orc.wav'
    output_filename_elf = 'output_elf.wav'

    change_voice(input_filename, output_filename_orc, voice_type='orc')
    print(f"Обработанный аудиофайл с голосом орка сохранен как {output_filename_orc}")

    change_voice(input_filename, output_filename_elf, voice_type='elf')
    print(f"Обработанный аудиофайл с голосом эльфа сохранен как {output_filename_elf}")


if __name__ == "__main__":
    main()
