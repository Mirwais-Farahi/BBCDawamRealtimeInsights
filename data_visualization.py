import matplotlib.pyplot as plt
import seaborn as sns


def plot_data_quality_issues(error_counts):
    labels = list(error_counts.keys())
    counts = list(error_counts.values())

    fig, ax = plt.subplots()
    ax.barh(labels, counts)
    ax.set_xlabel('Number of Errors')
    ax.set_title('Data Consistency Errors')
    plt.tight_layout()
    return fig