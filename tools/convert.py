# -*- coding: utf-8 -*-

from PIL import Image

# make_color_transparent('../ontogenesis/assets/images/map/worldmap.jpg', (0, 0, 0), output='newmap.png')


def make_color_transparent(img, color, output=None):
    img = Image.open(img)
    img = img.convert("RGBA")

    # datas = img.getdata()
    data = img.load()

    width, height = img.size
    for y in range(height):
        for x in range(width):
            p = data[x, y]
            if p[0] == color[0] and p[1] == color[1] and p[2] == color[2]:
            # if data[x, y] == (255, 255, 255, 255):
                data[x, y] = (255, 255, 255, 0)

    # new_data = []
    # for item in datas:
    #     if item[0] == color[0] and item[1] == color[1] and item[2] == color[2]:
    #         new_data.append((255, 255, 255, 0))
    #     else:
    #         new_data.append(item)
    #
    # img.putdata(new_data)
    if output:
        img.save(output, 'PNG')
