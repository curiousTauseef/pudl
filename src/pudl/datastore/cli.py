"""A CLI for fetching public utility data from reporting agency servers."""

import argparse
import logging
import sys
import warnings

import pudl
import pudl.constants as pc
from pudl.datastore import datastore


def parse_command_line(argv):
    """
    Parse command line arguments. See the -h option.

    :param argv: arguments on the command line must include caller file name.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-q',
        '--quiet',
        dest='verbose',
        action='store_false',
        help="Quiet mode. Suppress download progress indicators and warnings.",
        default=True
    )
    parser.add_argument(
        '-z',
        '--zip',
        dest='unzip',
        action='store_false',
        help="Do not unzip downloaded data files.",
        default=True
    )
    parser.add_argument(
        '-c',
        '--clobber',
        action='store_true',
        help="Clobber existing zipfiles in the datastore if they exist.",
        default=False
    )
    parser.add_argument(
        '-d',
        '--datastore_dir',
        type=str,
        help="""Directory where the datastore should be located. (default:
        %(default)s).""",
        default=pudl.settings.init()['pudl_in']
    )
    parser.add_argument(
        '-s',
        '--sources',
        nargs='+',
        choices=pc.data_sources,
        help="""List of data sources which should be downloaded.
        (default: %(default)s).""",
        default=pc.data_sources
    )
    parser.add_argument(
        '-y',
        '--years',
        dest='years',
        nargs='+',
        help="""List of years for which data should be downloaded. Different
        data sources have differet valid years. If data is not available for a
        specified year and data source, it will be ignored. If no years are
        specified, all available data will be downloaded for all requested data
        sources.""",
        default=[]
    )
    parser.add_argument(
        '--no_download',
        '-n',
        action='store_false',
        dest='download',
        help="""Do not attempt to download fresh data from the original
        sources. Instead assume that the zipfiles or other original data is
        already present, and organize it locally.""",
        default=True)

    arguments = parser.parse_args(argv[1:])
    return arguments


def main():
    """Main function controlling flow of the script."""
    # Create a logger to output any messages we might have...
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        # More extensive test-like formatter...
        '%(asctime)s [%(levelname)8s] %(name)s:%(lineno)s %(message)s',
        # This is the datetime format string.
        "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    args = parse_command_line(sys.argv)

    # Generate a list of valid years of data to download for each data source.
    # If no years were specified, use the full set of valid years.
    # If years were specified, keep only th years which are valid for that
    # data source, and optionally output a message saying which years are
    # being ignored because they aren't valid.
    years_by_source = {}
    for source in args.sources:
        if not args.years:
            years_by_source[source] = pc.data_years[source]
        else:
            years_by_source[source] = [int(year) for year in args.years
                                       if int(year) in pc.data_years[source]]
            bad_years = [int(year) for year in args.years
                         if int(year) not in pc.data_years[source]]
            if args.verbose and bad_years:
                warnings.warn(f"Invalid {source} years ignored: {bad_years}.")

    pudl_settings = pudl.settings.init(pudl_in=args.datastore_dir)

    datastore.parallel_update(
        sources=args.sources,
        years_by_source=years_by_source,
        states=args.states,
        pudl_settings=pudl_settings,
        clobber=args.clobber,
        unzip=args.unzip,
        dl=args.download,
    )


if __name__ == '__main__':
    sys.exit(main())
