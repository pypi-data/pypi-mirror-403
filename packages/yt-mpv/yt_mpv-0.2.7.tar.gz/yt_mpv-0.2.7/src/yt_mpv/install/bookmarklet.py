"""
Bookmarklet generation and setup for yt-mpv
"""

import logging
import webbrowser

# Configure logging
logger = logging.getLogger("yt-mpv")


def get_js():
    """Get the JavaScript bookmarklet code."""
    play_only_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv://?url=' + originalUrl + '&archive=0&play=1';})()"
    )

    play_archive_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv://?url=' + originalUrl + '&archive=1&play=1';})()"
    )

    archive_only_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv://?url=' + originalUrl + '&archive=1&play=0';})()"
    )

    return (play_only_js, play_archive_js, archive_only_js)


def open_browser():
    """Open the hosted install docs page with bookmarklets."""
    docs_url = "https://bitplane.net/dev/python/yt-mpv/install/"
    play_only_js, play_archive_js, archive_only_js = get_js()

    try:
        logger.info(f"Opening bookmarklet page: {docs_url}")
        webbrowser.open(docs_url)
        print("\nIf your browser doesn't open automatically:")
    except Exception as e:
        logger.error(f"Could not open browser: {e}")
        print("Please open the install page manually and/or create bookmarks with the following URLs:")

    print(f"Install page: {docs_url}")
    print(f"MPV Play: {play_only_js}")
    print(f"MPV Play+Archive: {play_archive_js}")
    print(f"Archive Only: {archive_only_js}")

    return True
