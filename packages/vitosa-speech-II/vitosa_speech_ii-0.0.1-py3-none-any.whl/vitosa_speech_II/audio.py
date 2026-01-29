import librosa
from pydub import AudioSegment
from pydub.generators import Sine
from transformers import pipeline

def censor_audio_with_beep(audio_path, model, processor, words_with_labels, device):
    
    print("-"*10 "Calculating time (alignment)" "-"*10)
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model.student,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        device=device,
        return_timestamps="word"
    )
    
    result = pipe(audio_path)
    chunks = result['chunks']
    
    toxic_timestamps = []
    chunk_idx = 0
    num_chunks = len(chunks)
    
    for word, label in words_with_labels:
        clean_word = word.replace('<|startoftranscript|>', '').replace('<|transcribe|>', '').strip()
        if not clean_word: continue
            
        if chunk_idx < num_chunks:
            chunk = chunks[chunk_idx]
            timestamp = chunk['timestamp']
            
            if label == 1:
                toxic_timestamps.append(timestamp)
            
            chunk_idx += 1
            
    print('\nDone ✓\n')
    print("-"*10 "Processing cutting and merging audio" "-"*10)
    
    try:
        original_audio = AudioSegment.from_wav(audio_path)
    except:
        print("Error: Fail to load audio")
        return None

    final_audio = AudioSegment.empty()
    
    current_pos_ms = 0
    
    toxic_timestamps.sort(key=lambda x: x[0])
    
    for start, end in toxic_timestamps:
        start_ms = start * 1000
        end_ms = end * 1000
        
        if start_ms > current_pos_ms:
            clean_segment = original_audio[current_pos_ms:start_ms]
            final_audio += clean_segment
        
        duration_ms = end_ms - start_ms
        if duration_ms > 0:
            beep = Sine(1000).to_audio_segment(duration=duration_ms).apply_gain(-5)
            final_audio += beep
        
        current_pos_ms = max(current_pos_ms, end_ms)

    if current_pos_ms < len(original_audio):
        remaining_audio = original_audio[current_pos_ms:]
        final_audio += remaining_audio

    output_path = "censored_audio_clean.wav"
    final_audio.export(output_path, format="wav")
    print(f"\nDone ✓ \n File result save path: {output_path}")
    return output_path