from errno import EILSEQ
from multiprocessing.sharedctypes import Value
from webbrowser import get
import torch
import torchvision
import random
import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import transforms
from utils import get_counts

def color_grayscale_arr(arr, color=0):
    assert arr.ndim == 2
    dtype = arr.dtype
    h, w = arr.shape
    arr = np.reshape(arr, [h, w, 1])
    if color == 0:
        arr = np.concatenate([arr,
                            np.zeros((h, w, 2), dtype=dtype)], axis=2)
    elif color == 1:
        arr = np.concatenate([np.zeros((h, w, 1), dtype=dtype),
                            arr,
                            np.zeros((h, w, 1), dtype=dtype)], axis=2)
    elif color == 2:
        arr = np.concatenate([arr,
                            arr,
                            np.zeros((h, w, 1), dtype=dtype)], axis=2)
    elif color == 3:
        arr = np.concatenate([arr,
                            np.zeros((h, w, 1), dtype=dtype),
                            arr], axis=2)
    elif color == 4:
        arr = np.concatenate([np.zeros((h, w, 2), dtype=dtype),
                            arr], axis=2)

    return arr

colors = {0: 'red', 1: 'green', 2: 'yellow', 3: 'pink', 4: 'blue'}

class MNIST:

    def __init__(self, root, cfg, split='train', transform=None):
        random.seed(0)
        self.dataset = torchvision.datasets.MNIST(root, download=True, train=split=='train')
        self.random_idxs = random.sample(range(len(self.dataset)), int(len(self.dataset)*0.1))
        self.imgs = self.dataset.data[self.random_idxs]
        self.labels = self.dataset.targets[self.random_idxs]
        self.root = root
        self.split = split
        # if split == 'train':
        #     self.imgs = self.dataset.data
        #     self.labels = self.dataset.targets
        # elif split == 'val':
        #     self.imgs = self.dataset.data[:int(len(self.dataset.data)/2)]
        #     self.labels = self.dataset.targets[:int(len(self.dataset.data)/2)]
        # elif split == 'test':
        #     self.imgs = self.dataset.data[int(len(self.dataset.data)/2):]
        #     self.labels = self.dataset.targets[int(len(self.dataset.data)/2):]
        self.class_labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.transform = transform
        self.class_weights = get_counts(self.labels)

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img, label, old_idx = self.imgs[idx], self.labels[idx], self.random_idxs[idx]
        # filename = f"{self.root}/MNIST/{self.split}-{old_idx}.jpg"
        # img = Image.open(filename).convert('RGB')
        img = Image.fromarray(img.numpy(), mode="L").resize((224, 224))
        filename = f"{self.root}/MNIST/{self.split}-{old_idx}.jpg"
        if not os.path.exists(f"{self.root}/MNIST/"):
            os.makedirs(f"{self.root}/MNIST/")
        if not os.path.exists(filename):
            img.save(filename)
        if self.transform:
            img = self.transform(img)

        return {
            "image": img,
            "label": label,
            "domain": 0,
            "group": label, # since we dont have group labels for test set,
            "filename": filename
        }

class SVHN:

    def __init__(self, root, cfg, split='train', transform=None):
        self.dataset = torchvision.datasets.SVHN(root, download=True, split='train' if split == 'train' else 'test')
        self.random_idxs = random.sample(range(len(self.dataset)), int(len(self.dataset)*0.1))
        self.root = root
        self.split = split
        self.imgs = self.dataset.data[self.random_idxs]
        self.labels = self.dataset.labels[self.random_idxs]
        # if split == 'train':
        #     self.imgs = self.dataset.data
        #     self.labels = self.dataset.labels
        # elif split == 'test':
        #     self.imgs = self.dataset.data[:int(len(self.dataset.data)/2)]
        #     self.labels = self.dataset.labels[:int(len(self.dataset.data)/2)]
        self.class_labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.transform = transform
        self.class_weights = get_counts(self.labels)

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img, label, old_idx = self.imgs[idx], self.labels[idx], self.random_idxs[idx]
        # filename = f"{self.root}/SVHN/{self.split}-{old_idx}.jpg"
        # img = Image.open(filename).convert('RGB')
        img = Image.fromarray(np.transpose(img, (1, 2, 0))).resize((224, 224))
        filename = f"{self.root}/SVHN/{self.split}-{old_idx}.jpg"
        if not os.path.exists(filename):
            img.save(filename)
        if self.transform:
            img = self.transform(img)

        return {
            "image": img,
            "label": label,
            "domain": 1,
            "group": label, # since we dont have group labels for test set
            "filename": filename,
        }

class ColoredMNISTSimplified:

    def __init__(self, root, cfg, split='train', transform=None):
        self.root = root
        self.split = split
        self.transform = transform
        self.cfg = cfg
        if cfg.DATA.CONFOUNDING == 1.0 and self.split == 'train':
            try:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}_100.npy', allow_pickle=True).item()
            except:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}_biased.npy', allow_pickle=True).item()

        if cfg.DATA.CONFOUNDING == 1.0 and self.split == 'val':
            try:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}_100.npy',
                                    allow_pickle=True).item()
            except:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}_biased.npy',
                                    allow_pickle=True).item()

        if cfg.DATA.CONFOUNDING == 1.0 and self.split == 'test':
            try:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}_100.npy',
                                    allow_pickle=True).item()
            except:
                self.data = np.load(f'{root}/ColoredMNIST/{split}_{self.cfg.DATA.BIAS_TYPE}.npy',
                                    allow_pickle=True).item()
        self.imgs = self.data['images']
        self.labels = self.data['labels']
        self.domains = self.data['colors']
        self.domains = np.array([np.where(np.unique(self.domains) == d)[0][0] for d in self.domains])
        print(self.imgs.shape, self.labels.shape, self.domains.shape)
        if self.cfg.DATA.BIAS_TYPE == 'quinque':
            self.colors = {0: 'red', 1: 'green', 2: 'yellow', 3: 'pink', 4: 'blue'}
            self.groups = np.array([np.array([r*5 + i for i in range(5)]) for r in range(10)])
        elif self.cfg.DATA.BIAS_TYPE == 'binary':
            self.colors = {0: 'red', 1: 'green'}
            self.groups = np.array([np.array([r*2 + i for i in range(2)]) for r in range(10)])
        # else: raise ValueError(f"{self.cfg.DATA.BIAS_TYPE} not a valid bias type.")
        else:
            self.colors = {0: 'red', 1: 'blue'}
            self.groups = np.array([np.array([r*2 + i for i in range(2)]) for r in range(10)])
        self.class_labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        if self.cfg.DATA.SHRINK:
            self.imgs, self.labels, self.domains = self.filter()
        self.class_weights = get_counts(self.labels)

    def filter(self):
        np.random.seed(0)
        filtered_im, filtered_label, filtered_dom = [], [], []
        for (im, label, dom) in zip(self.imgs, self.labels, self.domains):
            filtered_im.append(im)
            filtered_label.append(label)
            filtered_dom.append(dom)
        # take a sample so things run faster
        print(len(filtered_im), len(filtered_dom))
        sample_idxs = np.random.choice(np.array(list(range(len(filtered_im)))), int(0.5 * len(filtered_im)))
        filtered_im = �������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������