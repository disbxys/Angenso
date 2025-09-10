from AniListPy.anilistpy import AniList

from api import APIHandler
from utils.logging import get_logger

class AniListAPIHandler(APIHandler):
    def __init__(self) -> None:
        super().__init__()

        self.client = AniList()
        self._logger = get_logger(__name__, write_to_file=True)

    def get_all(self, start_page, media_type, all_: bool = False, retry_once: bool = True):
        errored_pages = []
        page = start_page

        # (page <= self.DEFAULT_PAGE_LIMIT) is used over
        # (page <= start_page+self.DEFAULT_PAGE_LIMIT) is because the program
        # assumes that this clause will only be used when looking at the first
        # x number of pages for new entries.
        while all_ or (page <= self.DEFAULT_PAGE_LIMIT):
            self._logger.debug(f"Querying page {page}.")
            response = self.client.query_page(
                page_num=page,
                media_type=media_type.upper(),
                sort_new=True
            )
        
            if "errors" in response.keys():
                self._logger.error(f'Error occurred with AniList API on page {page}.')
                for error_msg in response["errors"]:
                    self._logger.error(f"Status Code {error_msg['status']} | {error_msg['message']}...")

                self._logger.error(f"Storing page {page} for later retry.")
                errored_pages.append(page)
                
                # Do not continue if next request will be empty. It is assumed that an
                # error will not occur until multiple api calls have already been made.
                if has_next_page:
                    page += 1
                else:
                    break

                continue

            try:
                current_page = response["data"]["Page"]["pageInfo"]["currentPage"]
                has_next_page = response["data"]["Page"]["pageInfo"]["hasNextPage"]
            except:
                print(response)
                raise

            for media_metadata in response["data"]["Page"]["media"]:
                # yield id, title, and the complete metadata
                # The id and title should easily accessible.
                yield (
                    media_metadata["id"],
                    media_metadata["title"]["romaji"],
                    media_metadata
                )

            # Do not continue if next request will be empty
            if has_next_page:
                page += 1
            else:
                break

        if retry_once:
            self.get_pages(errored_pages, media_type)

    def get_pages(self, pages, media_type):
        for page in pages:
            self._logger.debug(f"Retrying page {page}.")
            response = self.client.query_page(
                page_num=page,
                media_type=media_type,
                sort_new=True
            )
        
            if ("errors" not in response.keys()) and ("error" not in response.keys()):
                if ("errors" not in response.keys()) and ("error" not in response.keys()):
                    self._logger.error(f'Error occurred on retry with AniList API on page {page}.')
                    for error_msg in response["errors"]:
                        self._logger.error(f"Status Code {error_msg['status']} | {error_msg['message']}...")
                    continue

            current_page = response["data"]["Page"]["pageInfo"]["currentPage"]
            has_next_page = response["data"]["Page"]["pageInfo"]["hasNextPage"]

            for media_metadata in response["data"]["Page"]["media"]:
                # yield id, title, and the complete metadata
                # The id and title should easily accessible.
                yield (
                    media_metadata["id"],
                    media_metadata["title"]["romaji"],
                    media_metadata
                )


    
    @staticmethod
    def _scan_for_404(error_dict):
        return any(err_msg["status"] for err_msg in error_dict)