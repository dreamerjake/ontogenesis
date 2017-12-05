import argparse
import os

from Pillow import Image, ImageChops


def crop_directory(path='.', filetype=None, suffix='_resized', bg_pixel=(0, 0), output_format='PNG'):
    dirs = os.listdir(path)
    for item in dirs:
        filepath = os.path.join(path, item)
        if os.path.isfile(filepath):
            f, e = os.path.splitext(filepath)
            if filetype is None or e == filetype:
                try:
                    im = Image.open(filepath)
                except:
                    print('Found {} - skipping (could not read image file)'.format(filepath))
                    continue
                resized_filepath = f + suffix + e
                if not f.endswith(suffix) and not os.path.isfile(resized_filepath):
                    bg = Image.new(im.mode, im.size, im.getpixel(bg_pixel))
                    diff = ImageChops.difference(im, bg)
                    diff = ImageChops.add(diff, diff, 2.0, -100)
                    bbox = diff.getbbox()
                    if bbox:
                        im.crop(bbox).save(resized_filepath, output_format, quality=90)
                        print('Resized {} as {}'.format(f, resized_filepath))
                    else:
                        print('Found {} - skipping (no bbox)'.format(filepath))
                else:
                    print('Found {} - skipping (already resized)'.format(filepath))
            elif filetype and e != filetype:
                print('Found {} - skipping (wrong filetype)'.format(filepath))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--filetype')
    parser.add_argument('--suffix')
    parser.add_argument('--bg_pixel')
    parser.add_argument('--output_format')

    args, extras = parser.parse_known_args()

    crop_directory(**{k: v for k, v in vars(args).items() if v})
