import matplotlib.pyplot as plt


def save_pair_figure(gt_img, rm_img, out_path, title_left="GT", title_right="RM"):
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=150)

    axes[0].imshow(gt_img)
    axes[0].set_title(title_left)
    axes[0].axis("off")

    axes[1].imshow(rm_img)
    axes[1].set_title(title_right)
    axes[1].axis("off")

    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
