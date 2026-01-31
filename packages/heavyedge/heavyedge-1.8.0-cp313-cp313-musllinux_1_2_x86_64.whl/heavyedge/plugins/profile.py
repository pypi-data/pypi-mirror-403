"""Commands to process profiles."""

import pathlib
from importlib.metadata import entry_points

import numpy as np

from heavyedge.cli.command import Command, deprecate_command, register_command

PLUGIN_ORDER = 0.0


@register_command("prep", "Preprocess raw profiles")
class PrepCommand(Command):
    def add_parser(self, main_parser):
        prep = main_parser.add_parser(
            self.name,
            description="Preprocess raw profiles and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        prep.add_argument(
            "--type",
            choices=[ep.name for ep in entry_points(group="heavyedge.rawdata")],
            required=True,
            help="Type of the raw profile data.",
        )
        prep.add_argument("--name", help="Name to label output dataset.")
        prep.add_argument(
            "raw",
            type=pathlib.Path,
            help="Path to raw profile data.",
        )
        prep.add_config_argument(
            "--res",
            type=float,
            help=(
                "Spatial resolution of profile data, i.e., points per unit length. "
                "Length unit must match the profile height unit."
            ),
        )
        prep.add_config_argument(
            "--sigma",
            type=float,
            help="Standard deviation of Gaussian kernel.",
        )
        prep.add_config_argument(
            "--std-thres",
            type=float,
            help="Standard deviation threshold for contact point detection.",
        )
        prep.add_config_argument(
            "--fill-value",
            type=float,
            help=(
                "Value to fill profile after the contact point. "
                "If not passed, do not fill the profile. "
                "'nan' can be passed."
            ),
        )
        prep.add_config_argument(
            "--z-thres",
            type=float,
            help=(
                "Modified Z-score threshold for outlier detection. "
                "If not passed, outliers are not detected."
            ),
        )
        prep.add_config_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, load entire profiles.",
        )
        prep.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.api import prep
        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        raw_type = entry_points(group="heavyedge.rawdata")[args.type].load()
        raw = raw_type(args.raw)

        gen = prep(
            raw,
            args.sigma,
            args.std_thres,
            args.fill_value,
            args.z_thres,
            args.batch_size,
            lambda msg: self.logger.info(f"{args.output} : {msg}"),
        )

        # Get first result to determine M
        Ys, Ls, names = next(gen)
        M = len(Ys[0])
        with ProfileData(args.output, "w").create(M, args.res, args.name) as out:
            out.write_profiles(Ys, Ls, names)
            for Ys, Ls, names in gen:
                out.write_profiles(Ys, Ls, names)

        self.logger.info(f"Saved {out.path}")

    @staticmethod
    def is_invalid(profile):
        return (len(profile) == 0) or np.any(np.isnan(profile))


@deprecate_command("1.6", "filtering in preparation step (heavyedge prep command)")
@register_command("outlier", "Filter outlier profiles")
class OutlierCommand(Command):
    def add_parser(self, main_parser):
        outlier = main_parser.add_parser(
            self.name,
            description="Remove outlier profiles and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        outlier.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        outlier.add_config_argument(
            "--z",
            type=float,
            help="Modified Z-score threshold for outlier detection.",
        )
        outlier.add_argument(
            "-o", "--output", type=pathlib.Path, help="Output file path"
        )

    def run(self, args):
        from heavyedge import ProfileData
        from heavyedge.api import outlier

        self.logger.info(f"Removing outliers: {args.profiles}")

        with ProfileData(args.profiles) as data:
            _, M = data.shape()
            res = data.resolution()
            name = data.name()

            x = data.x()
            areas = []
            for i in range(len(data)):
                Y, L, _ = data[i]
                areas.append(np.trapezoid(Y[:L], x[:L]))
            is_outlier = outlier(np.array(areas), args.z)

            with ProfileData(args.output, "w").create(M, res, name) as out:
                for skip, Y, L, name in zip(
                    is_outlier,
                    data._file["profiles"],
                    data._file["len"],
                    data.profile_names(),
                ):
                    if not skip:
                        out.write_profiles(Y.reshape(1, -1), [L], [name])

        self.logger.info(f"Saved {out.path}")


@register_command("fill", "Fill profiles after the contact point")
class FillCommand(Command):
    def add_parser(self, main_parser):
        fill = main_parser.add_parser(
            self.name,
            description="Fill profiles after the contact point and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        fill.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        fill.add_config_argument(
            "--fill-value",
            type=float,
            help=(
                "Value to fill after the contact point (default=0). "
                " 'nan' can be passed."
            ),
        )
        fill.add_config_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not passed, all data are loaded at once.",
        )
        fill.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.api import fill
        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        if args.fill_value is None:
            args.fill_value = 0

        with ProfileData(args.profiles) as file:
            (_, M), res, name = file.shape(), file.resolution(), file.name()
            gen = fill(
                file,
                args.fill_value,
                args.batch_size,
                lambda msg: self.logger.info(f"{args.output} : {msg}"),
            )

            with ProfileData(args.output, "w").create(M, res, name) as out:
                for Ys, Ls, names in gen:
                    out.write_profiles(Ys, Ls, names)

        self.logger.info(f"Saved {out.path}")


@register_command("merge", "Merge profile data")
class MergeCommand(Command):
    def add_parser(self, main_parser):
        merge = main_parser.add_parser(
            self.name,
            description="Merge profile data and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        merge.add_argument(
            "profiles",
            nargs="+",
            type=pathlib.Path,
            help="Paths to preprocessed profile data in 'ProfileData' structure.",
        )
        merge.add_argument("--name", help="Name to label output dataset.")
        merge.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, load entire profiles.",
        )
        merge.add_argument("-o", "--output", type=pathlib.Path, help="Output file path")

    def run(self, args):
        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        with ProfileData(args.profiles[0]) as data:
            _, M = data.shape()
            res = data.resolution()

        with ProfileData(args.output, "w").create(M, res, args.name) as out:
            for p in args.profiles:
                with ProfileData(p) as data:
                    if args.batch_size is not None:
                        for i in range(0, data.shape[0], args.batch_size):
                            out.write_profiles(*data[i : i + args.batch_size])
                    else:
                        out.write_profiles(*data[:])

        self.logger.info(f"Saved {out.path}")


@register_command("filter", "Filter profile data")
class FilterCommand(Command):
    def add_parser(self, main_parser):
        filter_parser = main_parser.add_parser(
            self.name,
            description="Filter profile data and save as hdf5 file.",
            epilog="The resulting hdf5 file is in 'ProfileData' structure.",
        )
        filter_parser.add_argument(
            "profiles",
            type=pathlib.Path,
            help="Path to preprocessed profile data in 'ProfileData' structure.",
        )
        filter_parser.add_argument(
            "index",
            type=pathlib.Path,
            help="Path to index npy file for filtering.",
        )
        filter_parser.add_argument("--name", help="Name to label output dataset.")
        filter_parser.add_argument(
            "--unsorted",
            action="store_true",
            help="Pass this flag if index is not sorted.",
        )
        filter_parser.add_argument(
            "--batch-size",
            type=int,
            help="Batch size to load data. If not provided, load entire profiles.",
        )
        filter_parser.add_argument(
            "-o", "--output", type=pathlib.Path, help="Output file path"
        )

    def run(self, args):
        from operator import itemgetter

        from heavyedge.io import ProfileData

        self.logger.info(f"Writing {args.output}")

        index = np.load(args.index)
        N = len(index)

        with ProfileData(args.profiles) as data:
            _, M = data.shape()
            res = data.resolution()

            with ProfileData(args.output, "w").create(M, res, args.name) as out:
                if args.batch_size is not None:
                    for i in range(0, N, args.batch_size):
                        idxs = index[i : i + args.batch_size]
                        if args.unsorted:
                            sorter = np.argsort(idxs)
                            unsorter = np.argsort(sorter)
                            data_sorted = data[idxs[sorter]]
                            data_unsorted = map(itemgetter(*unsorter), data_sorted)
                        else:
                            data_unsorted = data[idxs]
                        out.write_profiles(*data_unsorted)
                else:
                    idxs = index
                    if args.unsorted:
                        # sort idx, get profiles and sort back
                        sorter = np.argsort(idxs)
                        unsorter = np.argsort(sorter)
                        data_sorted = data[idxs[sorter]]
                        data_unsorted = map(itemgetter(*unsorter), data_sorted)
                    else:
                        data_unsorted = data[idxs]
                    out.write_profiles(*data_unsorted)

        self.logger.info(f"Saved {out.path}")
