import os, sys
import numpy as np
import pathlib
import argparse
import chainer

base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base, '../'))
from evaluation import load_inception_model

from PIL import Image
import numpy as np


def get_imagenet_samples(c=None):
    images = []
    count = 0
    for filename, label in train_filenames_and_labels:
        if c is not None and int(label) != c:
            continue
        image = np.array(Image.open(os.path.join(DATA_ROOT, filename)).convert('RGB')).astype(np.uint8)
        images.append(image)
        count += 1
    # Reference samples
    all_ref_samples = np.stack(images, axis=0).transpose((0, 3, 1, 2)).astype(np.float32)
    return all_ref_samples


def get_samples_filenames(c=None) -> list[pathlib.Path]:
    images = []
    for filename, label in train_filenames_and_labels:
        if c is not None and int(label) != c:
            continue
        images.append(os.path.join(DATA_ROOT, filename))
    return images


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu', '-g', type=int, default=0)
    parser.add_argument('--dataset', type=str, default='imagenet')
    parser.add_argument('--stat_dir_path', type=str, default='')
    parser.add_argument('--inception_model_path', type=str, default='')
    parser.add_argument('--n_classes', type=int, default=1000)
    parser.add_argument('--tf', action='store_true', default=False)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    chainer.cuda.get_device_from_id(args.gpu).use()

    DATA_ROOT = f'./datasets/{args.dataset}'
    LABEL_LIST_PATH = f'./datasets/image_list_{args.dataset}.txt'
    train_filenames_and_labels = np.loadtxt(LABEL_LIST_PATH, dtype=np.str_)

    get_samples = get_samples_filenames

    stat_dir = f'./datasets/{args.dataset}_stats'
    if not os.path.exists(stat_dir):
        os.makedirs(stat_dir)

    if args.tf:
        import source.inception.inception_score_tf
        from source.inception.inception_score_tf import get_mean_and_cov as get_mean_cov
    else:
        from evaluation import get_mean_cov
        model = load_inception_model(args.inception_model_path)

    # class-wise stats
    for c in range(args.n_classes):
        print('label:{}'.format(c))
        all_ref_samples = get_samples(c)
        if args.tf:
            mean, cov = get_mean_cov(all_ref_samples)
        else:
            with chainer.using_config('train', False), chainer.using_config('enable_backprop', False):
                mean, cov = get_mean_cov(model, all_ref_samples)
        np.savez(os.path.join(stat_dir, '{}.npz'.format(int(c))), mean=mean, cov=cov)

    # full stats
    all_ref_samples = get_samples()
    if args.tf:
        mean, cov = get_mean_cov(all_ref_samples)
    else:
        with chainer.using_config('train', False), chainer.using_config('enable_backprop', False):
            mean, cov = get_mean_cov(model, all_ref_samples)
    np.savez(os.path.join(stat_dir, 'full.npz'), mean=mean, cov=cov)