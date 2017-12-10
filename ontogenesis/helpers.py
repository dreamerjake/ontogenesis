# -*- coding: utf-8 -*-

from math import sqrt


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


def get_closest_sprite(group, pos, radius=None, get_range=False):
    if radius:
        distances = {}
        for sprite in group:
            distance = calc_dist(sprite.pos, pos)
            if distance < radius:
                distances[sprite] = distance
    else:
        distances = {sprite: calc_dist(sprite.pos, pos) for sprite in group}
    closest_sprite = min(distances, key=distances.get) if distances else None
    if get_range:
        return closest_sprite, distances[closest_sprite]
    return closest_sprite

