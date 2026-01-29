import torch
import time
import librosa
from huggingface_hub import hf_hub_download
from transformers import WhisperProcessor
from .model import WhisperToxicSpansKDModel
from .utils import group_tokens_into_words_corrected

def load_my_model(device, repo_id="ViToSAResearch/PhoWhisper-BiLSTM-CRF", model_filename="model.pth"):
    print(f"Loading model from {repo_id}...")
    checkpoint_path = hf_hub_download(repo_id=repo_id, filename=model_filename)
    
    model = WhisperToxicSpansKDModel(use_crf=True, kd_layers=[4, 8, 12])
    processor = WhisperProcessor.from_pretrained("Huydb/phowhisper-toxic", language="vietnamese", task="transcribe")
    
    state_dict = torch.load(checkpoint_path, map_location=device)
    new_state_dict = {k: v for k, v in state_dict.items() if 'teacher.' not in k}
    model.load_state_dict(new_state_dict, strict=False)
    model.to(device)
    model.eval()
    return model, processor

def toxic_span_asr_inference(audio_path: str, model, whisper_processor, device):
    timings = {}
    print( "-"*10 f"Processing audio file: {audio_path} " "-"*10)
    
    start_time = time.perf_counter()
    speech_array, sampling_rate = librosa.load(audio_path, sr=16000)
    input_features = whisper_processor(speech_array, sampling_rate=sampling_rate, return_tensors="pt").input_features
    
    with torch.no_grad():
        start_time = time.perf_counter()
        predicted_ids = model.student.generate(input_features.to(device))[0] 
        if device.type == 'cuda':
            torch.cuda.synchronize()
        timings["2_asr_inference"] = time.perf_counter() - start_time
    
    transcribed_text = whisper_processor.tokenizer.decode(predicted_ids, skip_special_tokens=True)
    
    input_ids_for_toxic = predicted_ids.unsqueeze(0).to(device)
    attention_mask_for_toxic = torch.ones_like(input_ids_for_toxic)
    
    with torch.no_grad():
        start_time = time.perf_counter()
        toxic_labels_list = model.predict(input_ids_for_toxic, attention_mask_for_toxic)
        if device.type == 'cuda':
            torch.cuda.synchronize()
        timings["3_toxic_span_inference"] = time.perf_counter() - start_time
        
        toxic_labels = toxic_labels_list[0] if isinstance(toxic_labels_list, list) else toxic_labels_list

    return transcribed_text, predicted_ids, toxic_labels, timings


def return_labels(audio_file,model,processor,device):
    text, pred_ids, labels, execution_times = toxic_span_asr_inference(audio_file, model, processor, device)

    words_with_labels = group_tokens_into_words_corrected(pred_ids, labels, processor.tokenizer)
    return words_with_labels