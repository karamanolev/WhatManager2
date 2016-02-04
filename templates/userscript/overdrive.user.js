// ==UserScript==
// @name OverDrive Tracker Search
// @namespace https://karamanolev.com
// @version 0.0.3
// @description Integration between OverDrive and torrent trackers
// @match http://localhost/*
// @match http://*.overdrive.com/*
// @grant GM_xmlhttpRequest
// @updateURL {{ root }}/userscript/overdrive.user.js
// @require http://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js
// ==/UserScript==

var bibliotikSearchProxyUrl = '{{ root }}/books/bibliotik/json/search';
var whatSearchProxyUrl = '{{ root }}/json/what_proxy';
var closeCurrentResults = function () {
}

$(document).keyup(function (e) {
    if (e.keyCode == 27) {
        closeCurrentResults();
    }
});

function listWindowMaker($this) {
    var result = {
    }
    var $div = $('<div></div>');
    result.putContent = function (content) {
        $div.empty();
        $div.append(content);
    }
    $div.css({
        position: 'absolute',
        left: $this.closest('.block-grid').find('.mobile-two:first .containAll').position().left,
        zIndex: 100,
        background: 'white',
        width: $this.closest('ul.block-grid').width() - 18,
        margin: '-10px 0 10px 0',
        padding: 10,
        border: '1px solid #ddd'
    });
    $this.append($div);

    closeCurrentResults();
    closeCurrentResults = function () {
        closeCurrentResults = function () {
        }
        $div.remove();
    }
    return result;
}

function detailsWindowMaker($this) {
    var result = {
    }
    var $div = $('<div></div>');
    result.putContent = function (content) {
        $div.empty();
        $div.append(content);
    }
    $div.css({
        background: 'white',
        width: 949,
        margin: '13px 7px -40px 0',
        border: '1px solid #ddd',
        padding: 10
    });
    $this.after($div);

    closeCurrentResults();
    closeCurrentResults = function () {
        closeCurrentResults = function () {
        }
        $div.remove();
    }
    return result;
}

function whatSearchHandler(query, callback) {
    GM_xmlhttpRequest({
        method: 'GET',
        url: whatSearchProxyUrl + '?action=browse&filter_cat%5B3%5D=1&searchstr=' + encodeURIComponent(query),
        onload: function (response) {
            callback($.parseJSON(response.responseText));
        },
        onerror: function (response) {
            callback(null);
        },
    });
}

function stealBibliotikSessionId(callback) {
    var extensionId = "opapngdimmnncheoehlpdnceakheghcn";
    var timeoutID = setTimeout(function () {
        alert('Please make sure the extension is installed and working.');
    }, 1000);
    chrome.runtime.sendMessage(extensionId, "stealBibliotikId", function (response) {
        clearTimeout(timeoutID);
        if (response == null) {
            alert('The extension could not find the session ID. Make sure you are logged in Bibliotik.');
        }
        callback(response);
    });
}

function bibliotikSearchHandler(query, callback) {
    stealBibliotikSessionId(function (sessionId) {
        var url = bibliotikSearchProxyUrl;
        url += '?query=' + encodeURIComponent(query);
        url += '&bibliotik_id=' + encodeURIComponent(sessionId);
        GM_xmlhttpRequest({
            method: 'GET',
            url: url,
            onload: function (response) {
                if (response.status == 200) {
                    callback($.parseJSON(response.responseText));
                } else {
                    callback(null);
                }
            },
            onerror: function (response) {
                callback(null);
            },
        });
    });
}

function whatOutputFormatter(response) {
    var $table = $('<table width="100%"></table>');
    $table.append('<tr><td colspan="2"><h6>What.CD Search Results</h6></td></tr>');
    if (response) {
        $.each(response.response.results, function (i, result) {
            var url = 'https://what.cd/torrents.php?id=' + result.groupId + '&torrentid=' + result.torrentId + '#torrent' + result.torrentId;
            var row = $('<tr><td class="title"><a target="_blank"></a></td><td class="tags"></td></tr>');
            row.find('.title a').text(result.groupName).attr('href', url);
            row.find('.tags').text(result.tags.join(', '));
            $table.append(row);
        });
        if (!response.response.results.length) {
            $table.append('<tr><td colspan="2">No results returned from What.CD</td></tr>');
        }
    } else {
        $table.append('<tr><td colspan="2"><b>Error!</b></td></tr>');
    }
    return $table;
}

function bibliotikOutputFormatter(response) {
    function getName(i) {
        return i.name;
    }

    var $table = $('<table width="100%"></table>');
    $table.append('<tr><td colspan="2"><h6>Bibliotik.me Search Results</h6></td></tr>');
    if (response) {
        $.each(response.results, function (i, result) {
            var url = 'https://bibliotik.me/torrents/' + result.id;
            var row = $('<tr><td class="title"><a target="_blank"></a></td><td class="tags"></td></tr>');
            if (result.type != 'Ebooks') {
                row.css('opacity', 0.5);
            }
            var title = '[' + result.type + '] ' + result.title;
            title += ' by ' + $.map(result.authors, getName).join(', ');
            title += ' [' + result.year + '] [' + result.format + ']';
            row.find('.title a').text(title).attr('href', url);
            if (result.retail) {
                row.find('.title a').append(' <b>[Retail]</b>');
            }
            row.find('.tags').text($.map(result.tags, getName).join(', '));
            $table.append(row);
        });
        if (!response.results.length) {
            $table.append('<tr><td colspan="2">No results returned from Bibliotik.me</td></tr>');
        }
    } else {
        $table.append('<tr><td colspan="2"><b>Error!</b></td></tr>');
    }
    return $table;
}

function createSearchWindow($this, windowMaker, searchIOs, initQuery) {
    var window = windowMaker($this);
    var $content = $('<div></div>');
    var $closeRow = $('<div><a href="#" class="close-button">[close]</a> <input type="text" class="query-string" /></div>');
    $closeRow.find('.close-button').on('click', function (e) {
        e.preventDefault();
        closeCurrentResults();
    });
    $closeRow.find('.query-string').css({
        display: 'inline',
        width: 400,
        height: 26,
    }).val(initQuery).on('keyup', function (e) {
        if (e.which == 13) {
            performSearch($(this).val());
        }
    });
    ;
    $content.append($closeRow);

    var $searchResults = $('<div></div>');
    $content.append($searchResults);

    var performSearch = function (query) {
        var $loadingRow = $('<p>Loading...</p>');
        $searchResults.empty();

        var completedIOs = 0;
        $.each(searchIOs, function (i, searchIO) {
            var $resultContainer = $('<div></div>');
            $searchResults.append($resultContainer);
            searchIO.searchHandler(query, function (resp) {
                $resultContainer.replaceWith(searchIO.outputFormatter(resp));

                ++completedIOs;
                if (completedIOs == searchIOs.length) {
                    $loadingRow.remove();
                }
            });
        });

        $searchResults.append($loadingRow);
    };

    window.putContent($content);
    performSearch(initQuery);
}

var allSearchIOs = [
    { searchHandler: whatSearchHandler, outputFormatter: whatOutputFormatter },
    { searchHandler: bibliotikSearchHandler, outputFormatter: bibliotikOutputFormatter }
];

function titleElement() {
    var $this = $(this);
    var type = $this.find('.borrow-button').data('format');
    if (type == 'eBook') {
        var author = $this.find('.tc-author').text();
        var title = $this.find('.borrow-button').data('title');
        var $searchButton = $('<a href="#" class="sample-button s-link"></a>');
        $searchButton.text('Trackers').on('click', function (e) {
            e.preventDefault();
            createSearchWindow($this, listWindowMaker, allSearchIOs, author + ' ' + title);
        });
        $this.find('div.feature-ul-contain').before($searchButton);
    }
}

function detailsElement() {
    var $this = $(this);
    var type = $this.find('span.tcc-icon-span').data('iconformat');
    if (type == 'eBook') {
        var author = $this.find('div#creatorDetails a').text();
        var title = $this.find('div#detailsTitle').text();
        var $searchButton = $('<div><a href="#" class="radius dtls-sample-button">What.CD</a></div>');
        $searchButton.on('click', function (e) {
            e.preventDefault();
            $searchButton.off('click').on('click', function (e) {
                e.preventDefault();
            });
            createSearchWindow($this, detailsWindowMaker, allSearchIOs, author + ' ' + title);
        }).css({
            textAlign: 'center',
            marginBottom: 5,
        }).find('a').css('width', 188);
        $this.find('img.wtil-cover').closest('div.row').append($searchButton);
    }
}

$('.title-element-li').each(titleElement);
$('div#allTheDetails').each(detailsElement);