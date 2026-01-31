import matplotlib.pyplot as plt
import numpy as np

def plot_veto_curve(snras_obj):
    """
    Generates a Veto Curve plot showing the SNRAS decay against noise.
    """
    dr_range = np.linspace(0.1, 5, 100)
    scores = []
    
    for dr in dr_range:
        s_in = dr * snras_obj.sigma_out
        temp_obj = SNRASCalculator(snras_obj.delta, snras_obj.sigma_out, s_in, snras_obj.n_points)
        scores.append(temp_obj.calculate_score())

    plt.figure(figsize=(10, 6))
    plt.plot(dr_range, scores, label='SNRAS Decay Curve', color='blue')
    plt.axvline(x=1, color='green', linestyle='--', label='Ideal Stability (Dr=1)')
    plt.xlabel('Dispersion Ratio (sigma_in / sigma_out)')
    plt.ylabel('SNRAS Score')
    plt.title('SNRAS Veto Effect Analysis')
    plt.legend()
    plt.grid(True)
    plt.show()