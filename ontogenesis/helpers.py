# -*- coding: utf-8 -*-

from math import sqrt


def render_outlined_text(text, font, font_color, outline_color):
    text_surface = font.render(text, True, font_color)
    final_surface = text_surface.copy()
    outline_surface = font.render(text, True, outline_color)
    for point in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        final_surface.blit(outline_surface, point)
    final_surface.blit(text_surface, (0, 0))
    return final_surface


def get_font_height(font):
    font_object = font.render('a', False, (0, 0, 0))
    return font_object.get_rect().height


def get_direction(angle, directions):
    num_directions = len(directions)
    degree = 360 / num_directions
    angle += degree / 2

    # print(f'directions: {num_directions}, degree:{degree}, angle: {angle}')

    for i, direction in enumerate(directions):
        if (i + 1) * degree > angle >= i * degree:
            return directions[i]
    else:
        return directions[0]


def require_methods(obj, method_list):
    for method in method_list:
        if not (method in dir(obj)) or not callable(getattr(obj, method)):
            raise Exception('Missing method {}'.format(method))


def require_attributes(obj, attribute_list):
    for attribute in attribute_list:
        if not hasattr(obj, attribute):
            raise Exception('Missing attribute {}'.format(attribute))


def calc_dist(point1, point2):
    dist = sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
    return dist


def get_closest_sprite(group, pos, radius=None, get_range=False, get_all=False):
    if radius:
        distances = {}
        for sprite in group:
            distance = calc_dist(sprite.pos, pos)
            if distance < radius:
                distances[sprite] = distance
    else:
        distances = {sprite: calc_dist(sprite.pos, pos) for sprite in group}
    if get_all:
        return distances
    closest_sprite = min(distances, key=distances.get) if distances else None
    if get_range:
        return closest_sprite, distances[closest_sprite]
    return closest_sprite

