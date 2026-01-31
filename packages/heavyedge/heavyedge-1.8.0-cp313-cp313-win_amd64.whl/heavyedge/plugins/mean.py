"""Commands to average profiles."""

import pathlib

from heavyedge.cli.command import Command, register_command

PLUGIN_ORDER = 0.1


@register_command("mean", "Compute mean profile")
class MeanCommand(Command):
    def add_parser(self, main_parser):
        mean = main_parser.add_parser(
            self.name,
            description="Compute Wasserstein mean profile and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        mean.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        mean.add_config_argument(
            "--wnum",
            type=int,
            help="Number of sample points to compute Wasserstein mean.",
        )
        mean.add_config_argument(
            "--fill-value",
            type=float,
            help=(
                "Value to fill after the contact point (default=0). "
                " 'nan' can be passed."
            ),
        )
        mean.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, loads entire profiles.",
        )
        mean.add_argument(
            "-o", "--output", type=pathlib.Path, help="Output npy file path"
        )

    def run(self, args):
        from heavyedge import ProfileData
        from heavyedge.api import mean_wasserstein

        self.logger.info(f"Writing {args.output}")

        if args.fill_value is None:
            args.fill_value = 0

        with ProfileData(args.profiles) as file:
            _, M = file.shape()
            res = file.resolution()
            name = file.name()

            with ProfileData(args.output, "w").create(M, res, name) as out:
                mean, L = mean_wasserstein(
                    file,
                    args.wnum,
                    args.batch_size,
                    lambda msg: self.logger.info(f"{out.path} : {msg}"),
                )
                mean[L:] = args.fill_value

                out.write_profiles(mean.reshape(1, -1), [L], [name])

        self.logger.info(f"Saved {out.path}.")
