import json
from pyquery import PyQuery as _


def pq_iter(pq):
    for e in pq:
        yield _(e)


def float_or(val, default=None):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_album_similar_albums(pq):
    albums = list()
    for album_item in pq_iter(pq('#similar-albums .album a')):
        album = {
            'url': album_item.attr('href'),
            'title': album_item('img').attr('alt')
        }
        title = album_item.attr('title')
        title_suffix = u' - ' + album['title']
        assert title.endswith(title_suffix)
        album['artists'] = title[0:-len(title_suffix)]

        albums.append(album)
    return albums


def parse_album(d):
    data = dict()
    pq = d.pq

    data['artist'] = {
        'name': pq('.album-artist a').text(),
        'url': pq('.album-artist a').attr('href')
    }
    data['title'] = pq('.album-title').text()
    data['review'] = pq('.review-body .editorial-text').html()
    data['rating'] = float_or(pq('.allmusic.rating').attr('data-stars'))
    data['release_date'] = pq('.details .release-date').text()
    data['duration'] = pq('.details .duration').text()
    data['album_art'] = json.loads(pq('div.album-art .image-container').attr('data-large'))
    data['similar_albums'] = parse_album_similar_albums(pq)
    data['genres'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.details .genres a')
    ]
    data['styles'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.details .styles a')
    ]
    data['moods'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.sidebar-module.moods a')
    ]
    data['themes'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.sidebar-module.themes a')
    ]

    data['medias'] = list()
    for media_title in pq_iter(pq('#tracks h2')):
        media = dict()
        media['name'] = media_title('.disc-num').text()
        data['medias'].append(media)
        media['tracks'] = list()
        for track_row in pq_iter(media_title.next()('tbody tr')):
            track = dict()
            track['position'] = track_row('td.tracknum').text()
            track['title'] = track_row('td.title div.title a').text()
            track['url'] = track_row('td.title div.title a').attr('href')
            media['tracks'].append(track)
            track['composers'] = list()
            track['duration'] = track_row('td.time').text()
            for composer in pq_iter(track_row('td.title div.artist a')):
                track['composers'].append({
                    'name': composer.text(),
                    'url': composer.attr('href'),
                })
            track['performers'] = list()
            for performer in pq_iter(track_row('td.performer div.primary a')):
                track['performers'].append({
                    'name': performer.text(),
                    'url': performer.attr('href')
                })
    return data


def parse_album_releases(d):
    data = dict()
    pq = d.pq
    data['releases'] = list()
    for e in pq_iter(pq('#album-releases tbody tr')):
        data['releases'].append({
            'format': e('.format').text(),
            'year': e('.year').text(),
            'title': e('.label strong').text(),
            'label': e('.label').text().replace(e('.label strong').text(), '').strip(),
        })
    return data


def parse_album_release(d):
    data = dict()
    pq = d.pq
    data['release_date'] = pq('#sidebar .details .release-date').text()
    data['label'] = pq('#sidebar .details .label').text()
    data['format'] = pq('#sidebar .details .format').text()
    data['flags'] = [f.text() for f in pq_iter(pq('#sidebar .details .flags li'))]
    data['catalog_number'] = pq('#sidebar .details .catalog').text()
    return data


def parse_artist(d):
    data = dict()
    pq = d.pq
    data['picture'] = pq('#sidebar .artist-image img').attr('src')
    data['review'] = pq('.review-body .editorial-text').html()
    data['genres'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.details .genres a')
    ]
    data['styles'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.details .styles a')
    ]
    data['active'] = pq('#sidebar dd.active').text()
    data['formed'] = pq('#sidebar dd.birth').text()
    # data['members'] = [
    #     {
    #         'name': m.text(),
    #         'url': m.attr('href')
    #     } for m in pq_iter(pq('#sidebar .group-members li a'))
    # ]
    data['moods'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.sidebar-module.moods a')
    ]
    data['themes'] = [
        {
            'name': _(e).text(),
            'url': _(e).attr('href')
        } for e in pq('.sidebar-module.themes a')
    ]
    data['discography'] = [
        {
            'year': e('.year').text(),
            'thumbnail': e('.thumbnail-img img').attr('src'),
            'title': e('.title a:first-child').text(),
            'url': e('.title a:first-child').attr('href'),
            'label': e('td.label .full-title').text(),
            'rating': float_or(e('td.ed-rating .allmusic.rating').attr('data-stars')),
        } for e in pq_iter(pq('#discography .album-table tbody tr'))
    ]
    data['photo_gallery'] = [
        json.loads(
            e.attr('data-large')
        ) for e in pq_iter(pq('#sidebar .media-gallery div.media-gallery-image.thumbnail'))
    ]
    return data


def parse_artist_related(d):
    pq = d.pq
    return {
        e('ul > h2').text(): [
            {
                'name': e2('li.secondary_link a').text(),
                'url': e2('li.secondary_link a').attr('href'),
            } for e2 in pq_iter(e('li.secondary_link'))
        ] for e in pq_iter(pq('#content .related-list li.related-item'))
    }


def parse_search(text):
    pq = _(text)
    return {
        'results': [
            {
                'thumbnail': r('div.image .thumbnail img').attr('src'),
                'title': r('div.title a').text(),
                'artist': {
                    'name': r('div.artist').text(),
                    'url': r('div.artist a').attr('href'),
                },
                'url': r('div.title a').attr('href'),
            } for r in pq_iter(pq('table.search-results tr'))
        ]
    }