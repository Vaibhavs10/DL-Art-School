import os

# script to find the latest directory in a directory and start tensorboard from there


def get_latest_dir(path):
    dirs = os.listdir(path)
    dirs = [os.path.join(path, d) for d in dirs]
    dirs = [d for d in dirs if os.path.isdir(d)]
    return max(dirs, key=os.path.getmtime)


def start_tensorboard(path):
    latest_dir = get_latest_dir(path)
    os.path.join(latest_dir, "tb_logger")
    os.system("tensorboard --logdir " + latest_dir)


if __name__ == "__main__":
    # process experiments folder
    print(
        "Starting tensorboard from latest experiment folder:"
        + get_latest_dir("experiments")
        + "..."
    )
    start_tensorboard("experiments")
