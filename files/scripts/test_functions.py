import time
import numpy as np
import scipy.signal as sp


def add(x, y):
    return x+y


def sub(x, y):
    return x-y


def multiply(x, y):
    return x*y


def sinus(x):
    return np.sin(x)


def wait(x):
    time.sleep(x)
    return x


def double(x, y):
    return x, y*2


def somme_quad(a, b, c, d):
    return a+b+c+d


def StateSpace(*system):
    sys1 = sp.StateSpace(*system)
    return sys1

def step(sys1):
    t, y = sp.step(sys1)
    return t, y

