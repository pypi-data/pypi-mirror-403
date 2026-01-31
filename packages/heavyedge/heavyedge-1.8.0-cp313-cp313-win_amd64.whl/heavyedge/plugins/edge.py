"""Commands for edge data manipulation."""

import pathlib

from heavyedge.cli.command import Command, register_command

PLUGIN_ORDER = 0.2


@register_command("scale", "Scale edge profiles")
class ScaleCommand(Command):
    def add_parser(self, main_parser):
        scale = main_parser.add_parser(
            self.name,
            description="Scale edge profiles.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        scale.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        scale.add_argument(
            "--type",
            choices=["area", "plateau"],
            default="area",
            help="Scaling type (default=area).",
        )
        scale.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, loads entire profiles.",
        )
        scale.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.api import scale_area, scale_plateau
        from heavyedge.io import ProfileData

        if args.type == "area":
            scale = scale_area
        elif args.type == "plateau":
            scale = scale_plateau
        else:
            raise NotImplementedError

        self.logger.info(f"Writing {args.output}")

        with ProfileData(args.profiles) as file:
            _, M = file.shape()
            res = file.resolution()
            name = file.name()

            with ProfileData(args.output, "w").create(M, res, name) as out:

                for scaled, Ls, names in scale(
                    file,
                    args.batch_size,
                    lambda msg: self.logger.info(f"{out.path} : {msg}"),
                ):
                    out.write_profiles(scaled, Ls, names)

        self.logger.info(f"Saved {out.path}.")


@register_command("trim", "Trim edge profiles")
class TrimCommand(Command):
    def add_parser(self, main_parser):
        trim = main_parser.add_parser(
            self.name,
            description="Trim edge profiles by a fixed width.",
            epilog=(
                "Width unit is determined by the resolution of 'profile'. "
                "The resulting hdf5 file is in 'ProfileData' structure."
            ),
        )
        trim.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        trim.add_config_argument(
            "--width",
            type=float,
            help="Edge width. If not passed, length of the shortest profile.",
        )
        trim.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, loads entire profiles.",
        )
        trim.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.api import trim
        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        with ProfileData(args.profiles) as file:
            _, M = file.shape()
            res = file.resolution()
            name = file.name()

            Ls = file._file["len"][:]
            if args.width is None:
                args.width = Ls.min() / res

            w1 = int(args.width * res)
            w2 = (M - Ls).min()
            with ProfileData(args.output, "w").create(w1 + w2, res, name) as out:

                for trimmed, Ls, names in trim(
                    file,
                    w1,
                    w2,
                    args.batch_size,
                    lambda msg: self.logger.info(f"{out.path} : {msg}"),
                ):
                    out.write_profiles(trimmed, Ls, names)

        self.logger.info(f"Saved {out.path}.")


@register_command("pad", "Pad edge profiles")
class PadCommand(Command):
    def add_parser(self, main_parser):
        pad = main_parser.add_parser(
            self.name,
            description="Pad edge profiles to a fixed width.",
            epilog=(
                "Width unit is determined by the resolution of 'profile'. "
                "The resulting hdf5 file is in 'ProfileData' structure."
            ),
        )
        pad.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        pad.add_config_argument(
            "--width",
            type=float,
            help="Edge width. If not passed, length of the shortest profile.",
        )
        pad.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, loads entire profiles.",
        )
        pad.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.api import pad
        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        with ProfileData(args.profiles) as file:
            _, M = file.shape()
            res = file.resolution()
            name = file.name()

            Ls = file._file["len"][:]
            if args.width is None:
                args.width = Ls.max() / res

            w1 = int(args.width * res)
            w2 = (M - Ls).min()
            with ProfileData(args.output, "w").create(w1 + w2, res, name) as out:

                for padded, Ls, names in pad(
                    file,
                    w1,
                    w2,
                    args.batch_size,
                    lambda msg: self.logger.info(f"{out.path} : {msg}"),
                ):
                    out.write_profiles(padded, Ls, names)

        self.logger.info(f"Saved {out.path}.")
