import numpy as np
import scipy as sci


class DCT:
    def __init__(self, data, cutoff_amount: int = None, range_width=None):
        self.coeffs = None
        self.find_coeffs(data, cutoff_amount)
        if range_width is not None:
            self.scale = range_width

    def __call__(self, *args, **kwargs):
        return self.numpy_func(*args, **kwargs)

    def find_coeffs(self, data, cutoff_amount: int = None):
        """
        Performs DCT on data, then create a cosine sum expression.
        Cut off all DCT coefficient less than thresh.
        Requires Sympy, Scipy, Numpy

        :param data: Discrete set of data
        :param cutoff_amount: Used instead of param 'thresh' to cut off coefficients. Keeps specified amount of coefficients
        :return: Cosine sum expression in sympy
        """

        # Преобразуем в numpy array, если пришел объект Pandas
        if hasattr(data, 'to_numpy'):
            data = data.to_numpy()
        else:
            data = np.asarray(data)

        coeffs = sci.fft.dct(data)
        indicies = list(range(0, len(coeffs)))
        indicies, _ = zip(*sorted(zip(indicies, coeffs), key=lambda x: np.abs(x[1]), reverse=True))
        for idx in indicies[cutoff_amount:]:
            coeffs[idx] = 0

        self.coeffs = coeffs

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, range_width):
        self._scale = (len(self.coeffs) - 1) / range_width

    def numpy_func(self, x, scaled=False):
        x = x * (self.scale if scaled else 1)
        N = len(self.coeffs)
        res = self.coeffs[0] / 2
        for n in range(1, N):
            res += self.coeffs[n] * np.cos((n / N * np.pi * (x + 1 / 2)))
        res *= (1 / N)

        return res
