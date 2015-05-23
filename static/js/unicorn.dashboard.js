/**
 * Convert number of bytes into human readable format
 *
 * @param integer bytes     Number of bytes to convert
 * @param integer precision Number of digits after the decimal separator
 * @return string
 */
function bytesToSize(bytes, precision) {
    function getPrecision(bytes) {
        if (bytes < 100) {
            return 2;
        } else {
            return 1;
        }
    }

    var kilobyte = 1024;
    var megabyte = kilobyte * 1024;
    var gigabyte = megabyte * 1024;
    var terabyte = gigabyte * 1024;
    var value;

    if ((bytes >= 0) && (bytes < kilobyte)) {
        return bytes + ' B';

    } else if ((bytes >= kilobyte) && (bytes < megabyte)) {
        value = bytes / kilobyte;
        return value.toFixed(getPrecision(value)) + ' KB';

    } else if ((bytes >= megabyte) && (bytes < gigabyte)) {
        value = bytes / megabyte;
        return value.toFixed(getPrecision(value)) + ' MB';

    } else if ((bytes >= gigabyte) && (bytes < terabyte)) {
        value = bytes / gigabyte;
        return value.toFixed(getPrecision(value)) + ' GB';

    } else if (bytes >= terabyte) {
        value = bytes / terabyte;
        return value.toFixed(getPrecision(value)) + ' TB';

    } else {
        return bytes + ' B';
    }
}

function getWhatId(link) {
    var regexps = [
        /torrents\.php\?action=download&id=(\d+)/,
        /torrents\.php\?.*torrentid=(\d+)/
    ];
    var result = null;
    $.each(regexps, function (i, r) {
        var m = link.match(r);
        if (m !== null) {
            result = m[1];
        }
    });
    return result;
}

function redirectShortly(link) {
    window.location = link;
}

$.fn.refreshTooltips = function () {
    this.find('.show-tooltip').tooltip({
        html: true
    });
    return this;
};

$.executeAndRepeat = function (interval, fn) {
    function inner(scheduleNew) {
        var started = new Date().getTime();
        fn(function () {
            var delay = new Date().getTime() - started;
            var nextTimeout = Math.max(0, interval - delay);
            if (scheduleNew !== false) {
                setTimeout(inner, nextTimeout);
            }
        });
    }

    $(function () {
        inner(true);
    });

    return function () {
        inner(false);
    }
};

$.fn.timedReload = function (url, interval, readyFn, getDataFn) {
    var $this = this;

    if (getDataFn === undefined) {
        getDataFn = function () {
            return undefined;
        };
    }

    if (readyFn === undefined) {
        readyFn = function () {
        };
    }

    return $.executeAndRepeat(interval, function (scheduleNext) {
        var data = getDataFn();
        if (data) {
            data = $.extend({
                'csrfmiddlewaretoken': csrfToken
            }, data)
        }
        $this.load(url, data, function (data) {
            scheduleNext();
            readyFn(data);
        });
    });
};


function stealBibliotikSessionId(callback) {
    var extensionId = "lmikggmhkhhfhancahkkdibafpcnbkno";
    var timeoutID = setTimeout(function () {
        alert('Please make sure the extension is installed and working.');
    }, 2000);
    chrome.runtime.sendMessage(extensionId, "stealBibliotikId", function (response) {
        clearTimeout(timeoutID);
        if (response == null) {
            alert('The extension could not find the session ID. Make sure you are logged in Bibliotik.');
        }
        callback(response);
    });
}
