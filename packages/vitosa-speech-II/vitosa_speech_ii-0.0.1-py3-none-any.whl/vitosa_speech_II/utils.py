import torch

def group_tokens_into_words_corrected(predicted_ids, toxic_labels, tokenizer):
    """
    Group token IDs to (decode)
    """
    words_with_labels = []
    
    if isinstance(predicted_ids, torch.Tensor):
        predicted_ids = predicted_ids.tolist()
    if isinstance(toxic_labels, torch.Tensor):
        toxic_labels = toxic_labels.tolist()
    
    raw_tokens = tokenizer.convert_ids_to_tokens(predicted_ids)
    
    current_word_ids = []
    current_label = -1 

    min_len = min(len(predicted_ids), len(toxic_labels))
    
    for i in range(min_len):
        token_id = predicted_ids[i]
        label = toxic_labels[i]
        raw_token = raw_tokens[i]
        
        if raw_token.startswith('Ġ') or i == 0:
            
            if current_word_ids:
                decoded_word = tokenizer.decode(current_word_ids).strip()
                if decoded_word: 
                    words_with_labels.append((decoded_word, current_label))
            
            current_word_ids = [token_id]
            current_label = label
        else:
            current_word_ids.append(token_id)
            current_label = max(current_label, label)

    if current_word_ids:
        decoded_word = tokenizer.decode(current_word_ids).strip()
        if decoded_word:
            words_with_labels.append((decoded_word, current_label))
        
    return words_with_labels