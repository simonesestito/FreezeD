import os, sys, time
import shutil
import numpy as np
import argparse
import chainer
from PIL import Image

base = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base, '../'))
from evaluation import gen_images_with_condition
import yaml
import source.yaml_utils as yaml_utils


def load_models(config):
    gen_conf = config.models['generator']
    gen = yaml_utils.load_model(gen_conf['fn'], gen_conf['name'], gen_conf['args'])
    return gen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, default='configs/base.yml')
    parser.add_argument('--gpu', '-g', type=int, default=0)
    parser.add_argument('--results_dir', type=str, default='./results/gans')
    parser.add_argument('--snapshot', type=str, default='')
    parser.add_argument('--rows', type=int, default=5)
    parser.add_argument('--columns', type=int, default=5)
    parser.add_argument('--classes', type=int, nargs="*", default=None)
    args = parser.parse_args()
    chainer.cuda.get_device_from_id(args.gpu).use()
    config = yaml_utils.Config(yaml.load(open(args.config_path), Loader=yaml.FullLoader))
    # Model
    gen = load_models(config)
    gen.to_gpu(args.gpu)
    out = args.results_dir
    chainer.serializers.load_npz(args.snapshot, gen)
    np.random.seed(1234)
    run = 20
    # classes = [35, 39, 12, 22, 43, 24, 41, 42, 51, 29, 59, 5, 31, 11, 20, 27, 32, 36, 61, 13, 0, 60, 44, 7, 34, 54, 6]
    classes = [56, 25, 16, 30, 49, 10, 6, 17, 1, 28, 21, 50, 37, 45, 14, 53]
    for c in classes:
        for i in range(run):
            with chainer.using_config('train', False), chainer.using_config('enable_backprop', False):
                x = gen_images_with_condition(gen, c=c, n=args.rows * args.columns, batchsize=args.rows * args.columns)
            _, _, h, w = x.shape
            x = x.reshape((args.rows, args.columns, 3, h, w))
            x = x.transpose(0, 3, 1, 4, 2)
            x = x.reshape((args.rows * h, args.columns * w, 3))

            save_path = os.path.join(out, 'class_{}_run_{}.png'.format(str(c), str(i)))
            if not os.path.exists(out):
                os.makedirs(out)
            Image.fromarray(x).save(save_path)


if __name__ == '__main__':
    main()
