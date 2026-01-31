import numpy as np

class SNRASCalculator:
    """
    SNRAS: Signal-to-Noise Ratio with Adjusted Stability.
    Developed by: Ahmed Sattar Jabbar.
    Reference: A&A Manuscript aa59231-26.
    """

    def __init__(self, delta, sigma_out, sigma_in, n_points):
        """
        Initialize the SNRAS parameters.
        :param delta: The transit depth (Signal amplitude).
        :param sigma_out: Standard deviation of the baseline noise.
        :param sigma_in: Standard deviation within the transit window.
        :param n_points: Number of data points in the transit.
        """
        self.delta = delta
        self.sigma_out = sigma_out
        self.sigma_in = sigma_in
        self.n_points = n_points

    def compute_penalty(self):
        """
        Calculate the Euclidean Penalty based on variance divergence.
        Formula: P = (sigma_in - sigma_out)^2 / sigma_out.
        """
        penalty = ((self.sigma_in - self.sigma_out)**2) / self.sigma_out
        return penalty

    def calculate_score(self):
        """
        Compute the final SNRAS score using the self-regulating formula.
        Formula: SNRAS = (delta * sqrt(N)) / (sigma_out + Penalty).
        """
        penalty = self.compute_penalty()
        denominator = self.sigma_out + penalty
        snras_score = (self.delta * np.sqrt(self.n_points)) / denominator
        return snras_score

    def get_traditional_snr(self):
        """
        Returns the traditional SNR for comparative analysis.
        """
        return (self.delta * np.sqrt(self.n_points)) / self.sigma_out