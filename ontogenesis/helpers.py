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
