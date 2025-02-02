import glob

from invoke import task
from invoke.exceptions import Exit

from .libs.common.color import color_message


def get_package_path(glob_pattern):
    package_paths = glob.glob(glob_pattern)
    if len(package_paths) > 1:
        raise Exit(code=1, message=color_message(f"Too many files matching {glob_pattern}: {package_paths}", "red"))
    elif len(package_paths) == 0:
        raise Exit(code=1, message=color_message(f"Couldn't find any file matching {glob_pattern}", "red"))

    return package_paths[0]


def _get_deb_uncompressed_size(ctx, package):
    # the size returned by dpkg is a number of bytes divided by 1024
    # so we multiply it back to get the same unit as RPM or stat
    return int(ctx.run(f'dpkg-deb --info {package} | grep Installed-Size | cut -d : -f 2 | xargs').stdout) * 1024


def _get_rpm_uncompressed_size(ctx, package):
    return int(ctx.run(f'rpm -qip {package} | grep Size | cut -d : -f 2 | xargs').stdout)


@task
def compare_size(ctx, new_package, stable_package, package_type, last_stable, threshold):
    mb = 1000000

    if package_type.endswith('deb'):
        new_package_size = _get_deb_uncompressed_size(ctx, get_package_path(new_package))
        stable_package_size = _get_deb_uncompressed_size(ctx, get_package_path(stable_package))
    else:
        new_package_size = _get_rpm_uncompressed_size(ctx, get_package_path(new_package))
        stable_package_size = _get_rpm_uncompressed_size(ctx, get_package_path(stable_package))

    threshold = int(threshold)

    diff = new_package_size - stable_package_size

    # For printing purposes
    new_package_size_mb = new_package_size / mb
    stable_package_size_mb = stable_package_size / mb
    threshold_mb = threshold / mb
    diff_mb = diff / mb

    if diff > threshold:
        print(
            color_message(
                f"""{package_type} size increase is too large:
  New package size is {new_package_size_mb:.2f}MB
  Stable package ({last_stable}) size is {stable_package_size_mb:.2f}MB
  Diff is {diff_mb:.2f}MB > {threshold_mb:.2f}MB (max allowed diff)""",
                "red",
            )
        )
        raise Exit(code=1)

    print(
        f"""{package_type} size increase is OK:
  New package size is {new_package_size_mb:.2f}MB
  Stable package ({last_stable}) size is {stable_package_size_mb:.2f}MB
  Diff is {diff_mb:.2f}MB (max allowed diff: {threshold_mb:.2f}MB)"""
    )
