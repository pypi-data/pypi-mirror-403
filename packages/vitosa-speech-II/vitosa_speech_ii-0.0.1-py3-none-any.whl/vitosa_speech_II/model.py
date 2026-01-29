import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import WhisperConfig, WhisperTokenizerFast, WhisperForConditionalGeneration
from torchcrf import CRF

class WhisperToxicSpansKDModel(nn.Module):
    def __init__(
        self,
        whisper_name: str = "Huydb/phowhisper-toxic",
        use_crf: bool = True,
        use_bidirectional = True,
        lstm_hidden: int = 512,
        dropout: float = 0.4,
        alpha_span: float = 0.5,
        alpha_kd: float = 0.5,
        kd_temp: float = 2.0,
        kd_layers: list = None,
        teacher_model=None
    ):
        super().__init__()
        # -- Student setup
        self.tokenizer = WhisperTokenizerFast.from_pretrained(
            whisper_name, language="vietnamese", task="transcribe", use_fast=True
        )
        config = WhisperConfig.from_pretrained(whisper_name)
        config.output_hidden_states = True  # enable hidden states
        self.student = WhisperForConditionalGeneration.from_pretrained(
            whisper_name, config=config
        )

        # -- KD teacher (CPU)
        self.teacher = teacher_model

        # -- Heads
        d_model = self.student.config.d_model
        self.dropout = nn.Dropout(dropout)
        self.use_crf = use_crf
        self.use_bidirectional = use_bidirectional
        if use_crf:
            if use_bidirectional:
                self.bilstm = nn.LSTM(
                    d_model, lstm_hidden // 2,
                    num_layers=1, batch_first=True, bidirectional=True
                )
                classifier_in_dim = lstm_hidden
            else:
                self.bilstm = nn.LSTM(d_model, lstm_hidden,
                      num_layers=1, batch_first=True, bidirectional=False)
                classifier_in_dim = lstm_hidden
            
            self.classifier = nn.Linear(classifier_in_dim, 2)
            self.crf = CRF(2, batch_first=True)
        else:
            self.classifier = nn.Linear(d_model, 2)

        # -- KD hyperparams
        self.alpha_span = alpha_span
        self.alpha_kd = alpha_kd
        self.temperature = kd_temp
        self.kd_layers = kd_layers or [4, 8, 12]

    def forward(
        self,
        input_ids,
        attention_mask,
        labels=None,
        teacher_input_ids=None,
        teacher_attention_mask=None
    ):
        device = next(self.student.parameters()).device
        ids = input_ids.to(device)
        mask = attention_mask.to(device)
        lab = labels.to(device) if labels is not None else None

        # 1) Student forward to get hidden states
        student_outputs = self.student.model.decoder(
            input_ids=ids,
            attention_mask=mask,
            output_hidden_states=True,
            return_dict=True
        )
        student_hiddens = student_outputs.hidden_states  # tuple of layer outputs

        # use top hidden for classification pipeline
        top_hidden = student_hiddens[-1]
        h = self.dropout(top_hidden)
        if self.use_crf:
            h, _ = self.bilstm(h)
        logits = self.classifier(h)

        loss = None
        if lab is not None:
            # span loss
            if self.use_crf:
                m = mask.clone().bool()
                m[:, 0] = True
                tags = lab.clone()
                tags[tags == -100] = 0
                span_loss = -self.crf(logits, tags, mask=m, reduction='mean')
            else:
                span_loss = nn.CrossEntropyLoss(ignore_index=-100)(
                    logits.view(-1, 2), lab.view(-1)
                )

            # KD loss: multi-depth
            kd_loss = 0.0
            if teacher_input_ids is not None and teacher_attention_mask is not None:
                # Teacher on CPU
                with torch.no_grad():
                    tch_out = self.teacher(
                        input_ids=teacher_input_ids,
                        attention_mask=teacher_attention_mask,
                        output_hidden_states=True,
                        return_dict=True
                    )
                teacher_hiddens = tch_out.hidden_states
                # compute layer-wise MSE
                for i in self.kd_layers:
                    s_feat = student_hiddens[i]
                    t_feat = teacher_hiddens[i]
                    # interpolate or project to same size if needed
                    kd_loss += F.mse_loss(s_feat, t_feat.to(device))
                kd_loss = kd_loss / len(self.kd_layers)
                loss = self.alpha_span * span_loss + self.alpha_kd * kd_loss
            else:
                loss = span_loss

        return {'loss': loss, 'logits': logits}

    def predict(self, input_ids, attention_mask):
        self.eval()
        with torch.no_grad():
            out = self.forward(input_ids, attention_mask)
        logits = out['logits']
        if self.use_crf:
            m = attention_mask.bool().to(next(self.student.parameters()).device)
            return self.crf.decode(F.log_softmax(logits, dim=-1), mask=m)
        return logits.argmax(dim=-1)