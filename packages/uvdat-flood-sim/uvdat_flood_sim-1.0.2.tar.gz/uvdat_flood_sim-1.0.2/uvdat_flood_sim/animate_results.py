import numpy

import matplotlib.pyplot as plt
import matplotlib.animation as ani


def animate(*, flood_results, output_path):
    n_frames = flood_results.shape[0]
    vmin, vmax = numpy.min(flood_results), numpy.max(flood_results)

    fig, ax = plt.subplots()
    im = ax.imshow(
        flood_results[0],
        cmap='viridis',
        vmin=vmin,
        vmax=vmax,
    )

    def update(i):
        ax.set_title(f'Hour={i + 1}')
        im.set_data(flood_results[i])
        return im

    animation = ani.FuncAnimation(fig, update, n_frames, interval=1000)
    animation.save(
        output_path,
        writer=ani.PillowWriter(fps=2)
    )

    plt.colorbar(im, label='Flood depth (m)')
    plt.show()
