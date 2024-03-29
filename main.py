from argparse import ArgumentParser
import json
from pathlib import Path

from api.anilisthandler import AniListAPIHandler
from api.myanimelisthandler import MyAnimeListAPIHandler
from utils.logging import get_logger

logger = get_logger(__name__, write_to_file=True)

def main(a:ArgumentParser):
    args = a.parse_args()

    dest = Path(args.destination)

    scrap_media(
        base_path=dest,
        datasource=args.datasource,
        media_type=args.media_type, 
        all_=args.all
    )

def scrap_media(
        base_path: Path,
        datasource: str,
        media_type: str = "ANIME",
        start_page: int = 1,
        all_: bool = False):

    if not isinstance(base_path, Path):
        base_path = Path(base_path).resolve()
    base_path.mkdir(parents=True, exist_ok=True)

    datasource_handler_dict = {
        "anilist": AniListAPIHandler,
        "myanimelist": MyAnimeListAPIHandler
    }
    api_handler = datasource_handler_dict[datasource]()

    log_template = "{status} {datasource} {id:<6} | <{title}>..."

    for uid, title, media_metadata in api_handler.get_all(start_page, media_type, all_=all_):
        # Build the filepath using the id as the filename
        dest_path = base_path / f"{uid}.json"

        # Keep a flag to check if the media entry is new or not
        is_existing_entry = dest_path.exists()

        # TODO: Skip old entries only if looking at new entries
        if (all_ != True) and is_existing_entry:
            # logger.debug(f'Skipped {uid:<6} | <{title}>...')
            logger.debug(log_template.format(
                status="Skipped",
                datasource=datasource,
                id=uid,
                title=title
            ))
            continue

        try:
            # Compare the data pulled to the existing copy
            # and skip if there is no difference
            if is_existing_entry:
                try:
                    with dest_path.open("r", encoding="utf-8") as infile:
                        local_data = json.load(infile)
                except json.decoder.JSONDecodeError:
                    # Since new data will be dumped to the file, there is no need
                    # to delete the file.
                    logger.debug(f"An empty file was discovered for {datasource} id: <{uid}>.")
                    local_data = dict()

                if media_metadata == local_data: continue

                # Update the local data with the new information
                # and save it
                local_data.update(media_metadata)
                media_metadata = local_data

            # Dump metadata to file
            with dest_path.open("w+", encoding="utf-8") as outfile:
                json.dump(media_metadata, outfile, indent=4, ensure_ascii=False)

            if all_ and is_existing_entry:
                # Updating existing media entry
                # logger.info(f'Updated {uid:<6} | <{title}>...')
                logger.info(log_template.format(
                    status="Updated",
                    datasource=datasource,
                    id=uid,
                    title=title
                ))
            else:
                # Adding new media entry
                # logger.info(f'Scrapped {uid:<6} | <{title}>...')
                logger.info(log_template.format(
                    status="Scrapped",
                    datasource=datasource,
                    id=uid,
                    title=title
                ))
        except KeyboardInterrupt:
            # Manual terminal of program
            logger.error("Program interrupted by keyboard shorcut.")
            raise
        except Exception:
            # TODO: Log what type of error occured
            logger.error("Error encountered when creating file {}.".format(dest_path.name))
            raise


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(
        "datasource", type=str, choices=["anilist", "myanimelist"],
        help="what datasource to search"
    )
    parser.add_argument(
        "media_type", choices=["anime", "manga"],
        help="what type of media"
    )
    parser.add_argument(
        "-d", "--destination", type=str, required=True,
        help="where to save files"
    )
    parser.add_argument(
        "-a", "--all", action="store_true",
        help="look at all entries"
    )

    main(parser)