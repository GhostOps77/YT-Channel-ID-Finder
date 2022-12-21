# This Python code can get you the channel ID of anybody's YT channel
# Just either from the url from one of their videos, their channel, playlists, etc.

# requires aiohttp (for Asychronous HTTP Requests)

from aiohttp import ClientSession
import asyncio
import re

# To check if its a valid YouTube URL (captures Playlist ID in Group 1)
REGEX_VALID_YT_URL = re.compile(r'^(?:https:\/\/)?(?:(?:m|www)\.)?youtu(?:be\.(?:[a-z]{2,3}\.?)+|\.be)\/(?:(?:watch|playlist)\?(?:.*?&)?(?:list=([\w\d-]+))?|(?:shorts|channel|user)\/|@[a-zA-Z\d]+)')

# Regex to obtain Channel ID from the meta tag in the /watch page
META_TAG_CHANNEL_ID_REGEX = re.compile(r'(?<=\<meta itemprop=\"channelId\" content=\")[^\"]+')

# Regex to obtain Channel ID from the link tag in the /watch page
LINK_TAG_CHANNEL_NAME_REGEX = re.compile(r'(?<=\<link itemprop=\"name\" content=\")[^\"]+')

# Regex to obtain the Channel name and ID of the owner of the Playlist from /playlist URL
PLAYLIST_OWNER_IN_PLAYLIST_PAGE_REGEX = re.compile(r'ownerText\":\{.*?text\":\"([^\"]+).*?ownerEndpoint\":\{.*?browseEndpoint\":{\"browseId\":\"([^\"]+)')

# Regex to obtain the Channel name and ID of the owner of the Playlist from /watch URL
PLAYLIST_OWNER_IN_WATCH_PAGE_REGEX = re.compile(r'ownerName\":\{\"simpleText\":\"([^\"]+)\".*?browseId\":\"([^\"]+)')

def meta_and_link_tag_infos(html_content): # Obtains Channel name from link tag, and Channel ID from meta tag
    return LINK_TAG_CHANNEL_NAME_REGEX.findall(html_content)[0], META_TAG_CHANNEL_ID_REGEX.findall(html_content)[0]

async def main(url):
    valid_url = REGEX_VALID_YT_URL.match(url)
    if not valid_url: # Raises TypeError if the given input is not a valid YouTube URL
        raise TypeError('Youtube URL not found')

    playlistID = valid_url.group(1) # Contains Playlist ID
    async with ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text() # Contains the Page Content

    if playlistID: # If the URL has a Playlist ID
        if playlistID == 'LL': # Liked Videos Playlist
            raise ValueError('This URL takes you to your Liked Videos Playlist')
        elif playlistID == 'WL': # Watch Later Playlist
            raise ValueError('This URL takes you to your Watch Later Playlist')
        else:
            if '/playlist?' in url: # To get Playlist Owner ID from the Playlist Page
                channelName, channelId = PLAYLIST_OWNER_IN_PLAYLIST_PAGE_REGEX.findall(html_content)[0]
                if '"contributorName":' in html_content:
                    # To check if the Channel Name in hte Playlist is mentioned with prefix 'by '
                    # (mentions the owner channel as a Contributor to the Playlist)
                    channelName = channelName.removeprefix('by ')

            else: # To get both the owner IDs of the playlist and the ongoing video
                print(f'Playlist detected: {playlistID}')
                playlistOwnerName, playlistOwnerId = PLAYLIST_OWNER_IN_WATCH_PAGE_REGEX.findall(html_content)[0]
                channelName, channelId = meta_and_link_tag_infos(html_content)

                print(f"Playlist belongs to channel: {playlistOwnerId}")

    else: # If the URL does not have a Playlist ID
        channelName, channelId = meta_and_link_tag_infos(html_content)

    return channelName, channelId # Channel Name & ID are returned here

def run(url):
    try:
        value = asyncio.run(main(url))
    except Exception:
        value = asyncio.get_event_loop().ensure_future(main(url))
    finally:
        return value


if __name__ == '__main__':
    ...
