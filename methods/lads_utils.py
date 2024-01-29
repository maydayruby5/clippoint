from audioop import bias
import os
from tkinter import N
from xml import dom

from click import pass_obj
import clip
import torch
import torch.nn as nn
import torch.nn.functional as nnf
import torch.backends.cudnn as cudnn

import wandb

import numpy as np
from tqdm import tqdm
from scipy.spatial import distance
import pandas as pd
from transformers import AdamW
import omegaconf
from omegaconf import OmegaConf

from clip_utils import zeroshot_classifier
try:
    from progress_bar import progress_bar
except:
    progress_bar = lambda current, total, msg: None

import uuid

def get_domain_text_embs(model, cfg, source_text_prompts, target_text_prompts, class_names):
    """
    Gets the text embeddings of the prompts describing the source and target domains. 
    If generic is True, source_text_prompts and target_text_prompts are strings instead of 
    templates to put the class name in. 
    """
    if cfg.AUGMENTATION.GENERIC:
        text_embeddings = zeroshot_classifier(target_text_prompts, model, normalize=cfg.METHOD.NORMALIZE, model_type=cfg.EXP.IMAGE_FEATURES)
        text_embeddings = np.transpose(text_embeddings, (1,0))
        orig_prompts = text_embeddings
        if len(source_text_prompts) > 0:
            source_embeddings = zeroshot_classifier(source_text_prompts, model, normalize=cfg.METHOD.NORMALIZE, model_type=cfg.EXP.IMAGE_FEATURES)
            print("source emb before averaging", source_embeddings.shape)
            source_embeddings = source_embeddings.mean(dim=0)
            print("source emb after averaging", source_embeddings.shape)
            diffs = torch.stack([emb-source_embeddings[0] for emb in text_embeddings])
            diffs /= text_embeddings.norm(dim=-1, keepdim=True)
    else:
        print(target_text_prompts)
        templates = target_text_prompts
        all_texts = []
        for t in source_text_prompts:
            texts = [[t.format(c)] for c in class_names]
            text_emb = zeroshot_classifier(texts, model, normalize=cfg.METHOD.NORMALIZE, model_type=cfg.EXP.IMAGE_FEATURES).T
            print(texts, "text_emb", text_emb.shape)
            all_texts.append(text_emb)
        if type(target_text_prompts[0]) == str:
            target_text_prompts = [target_text_prompts]
        print(target_text_prompts)
        for p in target_text_prompts:
            print(p)
            texts = [[t.format(c) for t in p] for c in class_names]
            text_emb = zeroshot_classifier(texts, model, normalize=cfg.METHOD.NORMALIZE, model_type=cfg.EXP.IMAGE_FEATURES).T
            all_texts.append(text_emb)
        # this subtracts the neutral embedding from the domain embeddings and normalizes. 
        text_pairs = torch.stack(all_texts)
        print("text pairs", text_pairs.shape)
        target_embeddings, source_embeddings = text_pairs, []
        if len(source_text_prompts) > 0:
            source_embeddings = text_pairs[:len(source_text_prompts)]
            target_embeddings = text_pairs[len(source_text_prompts):]
        else:
            source_embeddings = torch.zeros_like(target_embeddings)
        #     text_diffs = []
        #     source_domain = text_pairs[0]
        #     for target_domain in text_pairs[1:]:
        #         diff = target_domain - source_domain
        #         diff /= np.linalg.norm(diff, axis=-1, keepdims=True)
        #         # diff = np.expand_dims(diff, axis=0)
        #         text_diffs.append(diff)
        # else:
        #     target_embeddings = text_pairs
        #     text_diffs = text_pairs
        # diffs = torch.stack(text_diffs).permute(1,0,2) # should be (num_classes, num_domains, emb_size)
        # print("diffs shape", diffs.shape)
        # print("source embeddings", source_embeddings.shape)
        print("target embeddings", target_embeddings.shape)
    return source_embeddings, target_embeddings

class EmbeddingDataset:
    """
    Takes in CLIP embeddings (INPUTS), labels, and CLIP text embedding (TEXT_EMB of shape (num_domains, clip emb shape)).
    Weakly labels the domain using the text embeddings 
    TODO: try softlabels
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            