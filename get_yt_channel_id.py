# This Python code can get you the channel ID of anybody's YT channel
# Just either from the url from one of their videos, their channel, playlists, etc.

# Requires aiohttp (for asychronous requests)

from aiohttp import ClientSession
import asyncio
import re


# To check if its a valid YouTube URL (captures Youtube Domain in Group 1, Playlist ID in Group 2, and Video ID in embed URL in Group 3)
REGEX_VALID_YT_URL_DOMAIN = re.compile(r'^((?:https?:\/\/)?(?:(?:m|www)\.)?youtu(?:be(?:-nocookie)?\.(?!googleapis)(?:[a-z]{2,3}\.?)+|\.be)(?:\/|$))(?:.*?[?&]list=([\w\d-]+)|embed\/([\w\d-]+))?')

# Regex to obtain Channel ID from the meta tag
META_TAG_CHANNEL_ID_REGEX = re.compile(r'(?<=\<meta itemprop=\"channelId\" content=\")[^\"]+')

# Regex to obtain Channel ID from the meta tag
LINK_TAG_CHANNEL_NAME_REGEX = re.compile(r'(?<=\<link itemprop=\"name\" content=\")[^\"]+')

# Regex to obtain the Playlist name, Channel name and ID of the owner of the Playlist from /playlist URL
PLAYLIST_INFO_IN_PLAYLIST_PAGE_REGEX = re.compile(r'ownerText\":\{.*?text\":\"([^\"]+).*?browseEndpoint\":{\"browseId\":\"([^\"]+).*?playlistMetadataRenderer\":\{\"title\":\"([^\"]+)')

# Regex to obtain the Playlist name, Channel name and ID of the owner of the Playlist from /watch URL
PLAYLIST_INFO_IN_WATCH_PAGE_REGEX = re.compile(r'playlist\":\{\"title\":\"([^\"]+).*?ownerName\":\{\"simpleText\":\"([^\"]+)\".*?browseId\":\"([^\"]+)')

# Regex to obtain the Album Playlist name, Channel name and ID of the owner of the Playlist from /playlist URL
CHANNEL_AND_PLAYLIST_NAME_IN_ALBUM_PLAYLIST_PAGE_REGEX = re.compile(r'subtitle\":\{\"simpleText\":\"(.+?)(?= • Album"|").*?playlistMetadataRenderer\":\{\"title\":\"([^\"]+)')

# Regex to obtain Channel ID and name from embed Page URL
OWNER_CHANNEL_INFO_IN_EMBED_PAGE = re.compile(r'embeddedPlayerOverlayVideoDetailsExpandedRenderer\\\":\{\\\"title\\\":{\\\"runs\\\":\[\{\\\"text\\\":\\\"([^\\]+)\\\".*?channelId\\\":\\\"([^\\]+)\\\"')

# Regex to obtain the Album Playlist name, Channel name and ID of the owner of the Playlist from /watch URL
CHANNEL_AND_PLAYLIST_NAME_IN_ALBUM_PLAYLIST_WATCH_PAGE_REGEX = re.compile(r'playlistShareUrl.*?longBylineText\":\{\"runs\":\[\{\"text\":\"([^\"]+).*?browseId\":\"([^\"]+).*?titleText\":\{\"runs\":\[\{\"text\":\"([^\"]+)')


def meta_and_link_tag_infos(html_content:str): # Obtains Channel name from link tag, and Channel ID from meta tag
    return LINK_TAG_CHANNEL_NAME_REGEX.findall(html_content)[0], META_TAG_CHANNEL_ID_REGEX.findall(html_content)[0]


def findChannelID(url:str, html_content:str, playlistId:str):
    if playlistId: # If the URL has a Playlist ID
        if playlistId == 'LL': # Liked Videos Playlist
            raise ValueError('This URL takes you to your Liked Videos Playlist')

        elif playlistId == 'WL': # Watch Later Playlist
            raise ValueError('This URL takes you to your Watch Later Playlist')

        else:
            if '/playlist?' in url: # To get Playlist Owner ID from the Playlist Page
                if '"albumName":' in html_content: # To check if the given Playlist is an Album
                    channelName, playlistName = CHANNEL_AND_PLAYLIST_NAME_IN_ALBUM_PLAYLIST_PAGE_REGEX.findall(html_content)[0]

                    # Lazy Regex searching, Channel ID is in Group 1
                    channelId = next(iter(re.finditer(rf'\"{channelName}\".*?browseId\":\"([^\"]+)', html_content)))[1]

                else: # not an album
                    channelName, channelId, playlistName = PLAYLIST_INFO_IN_PLAYLIST_PAGE_REGEX.findall(html_content)[0]
                    if '"contributorName":' in html_content:
                        # To check if the Channel Name in the Playlist is mentioned with prefix 'by '
                        # (mentions the owner channel as a Contributor to the Playlist)
                        channelName = channelName.removeprefix('by ')

            else: # To get both the owner IDs of the Playlist and the Ongoing Video's Owners
                channelName, channelId = meta_and_link_tag_infos(html_content)

                if ':"ALBUM"' in html_content or 'OFFICIAL_ARTIST_BADGE' in html_content:
                    # To get Playlist details from the Currently Playing Album Playlist
                    playlistOwnerName, playlistOwnerId, playlistName = CHANNEL_AND_PLAYLIST_NAME_IN_ALBUM_PLAYLIST_WATCH_PAGE_REGEX.findall(html_content)[0]

                else: # To get Playlist details from Currently playing normal Playlist
                    playlistName, playlistOwnerName, playlistOwnerId = PLAYLIST_INFO_IN_WATCH_PAGE_REGEX.findall(html_content)[0]

                print(f"Playlist belongs to channel: {playlistOwnerId} ({playlistOwnerName})")
            print(f'Playlist ID: {playlistId} ({playlistName})')

    else: # If the URL does not have a Playlist ID
        channelName, channelId = meta_and_link_tag_infos(html_content)

    print(f"Channel ID: {channelId} ({channelName})") # Channel ID is shown here
    return channelId, channelName


async def main(url:str):
    validURL = REGEX_VALID_YT_URL_DOMAIN.findall(url)

    if not validURL: # Raises TypeError if the given input is not a valid YouTube URL
        raise TypeError('Youtube URL not found')

    parsedURL, playlistId, extras = validURL[0]

    if parsedURL == url and playlistId == '' and extras == '': # Raises ValueError if the main Domain URL is given as input
        raise ValueError("You've entered the main Domain URL of the YouTube")

    elif '/embed/' in url: # Fixes some request issues where the given embed URL shows "Video unavailable"
        url = url.replace('/embed/', '/watch?v=')

    async with ClientSession() as session: # Doing the HTTP Request here
        async with session.get(url, allow_redirects=True) as response:
            response_url = response.url # Redirected final URL
            html_content = await response.text() # HTML Content

            # Raises ValueError if the given YouTube URL doesn't exist
            if response_url == 'https://www.youtube.com/' or 'STYLE_HOME_FILTER' in html_content or '/error?src=404' in html_content:
              raise ValueError("This YouTube URL either doesn't exist")

            findChannelID(str(response_url), html_content, playlistId)


def run(url:str): # Pass the input in the URL parameter run(input()) or in main function
    try:
        value = asyncio.run(main(url))
    except Exception:
        value = asyncio.get_event_loop().ensure_future(main(url))
    finally:
        return value
