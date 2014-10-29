'use strict';

angular.
    module('whatify.player', []).
    factory('whatPlayer', function($rootScope) {
        var s = {
                isPlaying: false,
                currentTime: 0,
                duration: null
            },
            audio = document.createElement('audio'),
            aurora = null;

        function auroraDuration(time) {
            $rootScope.$apply(function() {
                s.duration = time / 1000;
            });
        }

        function auroraProgress(time) {
            $rootScope.$apply(function() {
                s.currentTime = time / 1000;
            });
        }

        function auroraEnd() {
            $rootScope.$apply(function() {
                $rootScope.$emit('songEnded');
            });
        }

        function bindAurora() {
            aurora.on('duration', auroraDuration);
            aurora.on('progress', auroraProgress);
            aurora.on('end', auroraEnd);
        }

        function unbindAurora() {
            aurora.off('duration', auroraDuration);
            aurora.off('progress', auroraProgress);
            aurora.off('end', auroraEnd);
        }

        $(audio).on('playing', function() {
            console.log('<audio>: playing');
            $rootScope.$apply(function() {
                s.isPlaying = true;
            });
        });
        $(audio).on('timeupdate', function() {
            $rootScope.$apply(function() {
                s.currentTime = audio.currentTime;
            });
        });
        $(audio).on('loadedmetadata', function() {
            console.log('<audio>: loadedmetadata');
            $rootScope.$apply(function() {
                s.duration = audio.duration;
            });
        });
        $(audio).on('ended', function() {
            console.log('<audio>: ended');
            $rootScope.$apply(function() {
                $rootScope.$emit('songEnded');
            });
        });
        $(audio).on('error', function(e) {
            console.log('<audio>: error');
            $rootScope.$apply(function() {
                s.isPlaying = false;
            });
        });
        s.play = function() {
            if (audio.src) {
                audio.play();
                s.isPlaying = true;
            } else if (aurora !== null) {
                aurora.play();
                s.isPlaying = true;
            }
        };
        s.load = function(src) {
            if (aurora !== null) {
                aurora.stop();
                unbindAurora();
                aurora = null;
            }
            if (audio.src) {
                audio.pause();
                audio.src = '';
                audio.removeAttribute('src');
            }
            s.isPlaying = false;
            s.currentTime = 0;
            s.duration = null;
            if (src) {
                if (src.toLowerCase().indexOf('.flac') != -1) {
                    aurora = AV.Player.fromURL(src);
                    bindAurora();
                } else if (src.toLowerCase().indexOf('.mp3') != -1) {
                    audio.src = src;
                } else {
                    console.error('Neither .mp3 nor .flac found in URL.');
                }
            }
        };
        s.pause = function() {
            if (audio.src) {
                s.isPlaying = false;
                audio.pause();
            } else if (aurora !== null) {
                s.isPlaying = false;
                aurora.pause();
            }
        };
        s.setVolume = function(volume) {
            audio.volume = volume;
            if (aurora !== null) {
                aurora.volume = Math.round(volume * 100);
            }
        };
        s.getVolume = function() {
            return audio.volume;
        };
        s.seek = function(time) {
            audio.currentTime = time;
        };
        return s;
    }).
    factory('whatPlaylist', function($rootScope, whatPlayer) {
        var s = {
            items: [],
            index: 0
        };
        var update = function() {
            if (s.index === 0) {
                s.currentItem = null;
            } else {
                s.currentItem = s.items[s.index - 1];
            }
            s.canForward = s.index !== 0 && s.index < s.items.length;
            s.canBackward = s.index > 1;
        };
        update();

        $rootScope.$on('songEnded', function() {
            if (s.canForward) {
                s.play(s.index + 1);
            } else {
                s.index = 1;
                update();
                whatPlayer.load(s.currentItem.url);
            }
        });
        s.clear = function() {
            s.items = [];
            s.index = 0;
            update();
            whatPlayer.load(null);
        };
        // using jQuery
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        var csrftoken = getCookie('csrftoken');
        function sameOrigin(url) {
            // test that a given url is a same-origin URL
            // url could be relative or scheme relative or absolute
            var host = document.location.host; // host + port
            var protocol = document.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (sameOrigin(settings.url)) {
                    // Send the token to same-origin, relative URLs only.
                    // Send the token only if the method warrants CSRF protection
                    // Using the CSRFToken value acquired earlier
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        s.play = function(index) {
            s.index = index;
            update();
            whatPlayer.load(s.currentItem.url);
            whatPlayer.play();
            $.post( window.location.href.replace(window.location.hash, '').replace('whatify','lastfm/scrobble'), JSON.stringify({ "artist": s.currentItem.metadata.artist, "title" : s.currentItem.metadata.title, "album" : s.currentItem.metadata.album }) );
        };
        s.add = function(item) {
            s.items.push(item);
            update();
        };
        s.forward = function() {
            if (!s.canForward) {
                return;
            }
            s.play(s.index + 1);
        };
        s.backward = function() {
            if (!s.canBackward) {
                return;
            }
            s.play(s.index - 1);
        };
        s.reorder = function(itemIds) {
            var itemsById = {};
            s.items.forEach(function(item) {
                itemsById[item.id] = item;
            });
            s.items = [];
            itemIds.forEach(function(id) {
                if (s.currentItem.id == id) {
                    s.index = s.items.length;
                }
                s.items.push(itemsById[id]);
            });
            update();
        };
        return s;
    }).
    controller('WhatPlayerController', function($scope, $rootScope, whatMeta, whatPlayer, whatPlaylist, whatifyNoty) {
        console.log('Create WhatPlayerController');
        $scope.player = whatPlayer;
        $scope.playlist = whatPlaylist;
        $scope.volume = whatPlayer.getVolume();
        $scope.$watch('volume', function(newValue) {
            whatPlayer.setVolume(newValue);
        });
        $scope.seek = function(time) {
            whatPlayer.seek(time);
        };
        $scope.playTorrentGroup = function(torrentGroup, index) {
            if (whatPlaylist.currentItem &&
                whatPlaylist.currentItem.torrentGroup.id == torrentGroup.id) {
                if (index === undefined) {
                    whatPlayer.play();
                    return;
                }
            }
            var inPlaylist = false;
            if (index !== undefined) {
                $.each(whatPlaylist.items, function(i, item) {
                    if (item.id == torrentGroup.playlist[index - 1].id) {
                        whatPlaylist.play(i + 1);
                        inPlaylist = true;
                        return false;
                    }
                });
            }
            if (!inPlaylist) {
                whatPlaylist.clear();
                $.each(torrentGroup.playlist, function(i, item) {
                    item.torrentGroup = torrentGroup;
                    whatPlaylist.add(item);
                });
                whatPlaylist.play(index || 1);
            }
        };
        $scope.downloadTorrentGroup = function(torrentGroupId) {
            if (confirm('Are you sure you want to download this?')) {
                whatMeta.downloadTorrentGroup($scope.torrentGroup.id).success(function(resp) {
                    if (resp.success) {
                        whatifyNoty.success('Downloading ' + $scope.torrentGroup.name);
                        $scope.$emit('torrentDownloading');
                    } else {
                        if (resp.error) {
                            whatifyNoty.error('Download failed: ' + resp.error);
                        } else {
                            whatifyNoty.error('Download failed without specified error');
                        }
                    }
                });
            }
        };
        $scope.copyTorrentGroupUrl = function(event, torrentGroup, index) {
            var item,
                objectName,
                url = window.location.href.replace(window.location.hash,
                        '#/torrentGroups/' + torrentGroup.id) + '/play';
            if (index === undefined) {
                objectName = torrentGroup.name
            } else {
                item = torrentGroup.playlist[index];
                objectName = item.metadata.title;
                url += '/' + (index + 1);
            }
            event.stopPropagation();
            $rootScope.$emit('showCopyLinkModal', {
                title: 'Play link for ' + objectName,
                url: url
            });
        }
    }).
    directive('wmPlayerSm', function() {
        return {
            templateUrl: templateRoot + '/player/player.html'
        }
    }).
    directive('volumeSlider', function() {
        function volumeToPercent(volume) {
            var value = Math.sqrt(volume);
            return value * 100;
        }

        function percentToVolume(percent) {
            var value = percent / 100;
            return value * value;
        }

        return {
            template: '<input type="text">',
            require: '?ngModel',
            link: function(scope, element, attrs, ngModel) {
                if (!ngModel) return;
                var slider = element.children().eq(0).slider({
                    min: 0,
                    max: 100,
                    value: volumeToPercent(ngModel.$viewValue || 0)
                });
                ngModel.$render = function() {
                    slider.slider('setValue', volumeToPercent(ngModel.$viewValue || 0), false);
                };
                function updateScope(ev) {
                    scope.$apply(function() {
                        ngModel.$setViewValue(percentToVolume(ev.value || 0));
                    });
                }

                slider.on('slide', updateScope).on('slideStart', updateScope);
            }
        }
    }).
    directive('seekSlider', function($filter) {
        var scale = 1000;
        return {
            template: '<input type="text">',
            require: '?ngModel',
            link: function(scope, element, attrs, ngModel) {
                var isSliding = false;

                function getDuration() {
                    return parseFloat(attrs.duration);
                }

                if (!ngModel) return;
                var slider = $(element.children()[0]).slider({
                    min: 0,
                    max: scale,
                    value: 0,
                    formatter: function() {
                        var duration = getDuration();
                        var time = 0;
                        if (duration) {
                            time = slider.slider('getValue') / scale * duration;
                        }
                        return $filter('asTime')(time);
                    },
                    enabled: false
                });
                ngModel.$render = function() {
                    var value;
                    var duration = getDuration();
                    if (isSliding) {
                        return;
                    }
                    if (duration) {
                        value = ngModel.$viewValue / duration;
                    } else {
                        value = 0;
                    }
                    slider.slider('setValue', value * scale, false);
                };
                slider.on('slideStart', function() {
                    isSliding = true;
                }).on('slideStop', function(ev) {
                    var value = ev.value || 0;
                    var duration = getDuration();
                    isSliding = false;
                    scope.seek(value / scale * duration);
                });
                attrs.$observe('duration', function() {
                    var duration = getDuration();
                    if (duration && !slider.slider('isEnabled')) {
                        slider.slider('enable');
                    } else if (!duration && slider.slider('isEnabled')) {
                        slider.slider('disable');
                    }
                });
            }
        }
    }).
    directive('artistList', function() {
        return {
            template: '<span ng-repeat="a in artists" ng-switch="a.id">' +
                '<span ng-switch-when="-1">{{ a.name }}{{ a.join }}</span>' +
                '<span ng-switch-default><a ng-href="#/artists/{{ a.id }}">{{ a.name }}</a>' +
                '{{ a.join }}</span></span>',
            scope: {
                artists: '='
            }
        }
    }).
    directive('sortablePlaylist', function() {
        return {
            link: function(scope, element, attrs) {
                element.multisortable({
                    items: '> tr',
                    stop: function(event, ui) {
                        var ids = $.map(element.children(), function(e) {
                            return $(e).data('item-id');
                        });
                        scope.$apply(function() {
                            scope.playlist.reorder(ids);
                        });
                    }
                });
            }
        }
    }).
    directive('currentItemSidebar', function() {
        return {
            templateUrl: templateRoot + '/player/currentItemSidebar.html',
            scope: {
                item: '='
            }
        }
    }).
    directive('playingFormatDisplay', function(whatPlaylist) {
        return {
            template: '<img ng-src="{{ playingFormatSrc }}" ng-if="showPlayingFormat"' +
                ' style="width: 60px; height: 30px;">' +
                '<div style="width: 60px; height: 30px;" ng-if="!showPlayingFormat"></div>',
            scope: {
                item: '='
            },
            controller: function($scope) {
                $scope.showPlayingFormat = false;
                $scope.$watch('item', function() {
                    if ($scope.item) {
                        if ($scope.item.url.indexOf('.flac') !== -1) {
                            $scope.showPlayingFormat = true;
                            $scope.playingFormatSrc = '../static/img/logo-flac.png';
                        } else if ($scope.item.url.indexOf('.mp3') !== -1) {
                            $scope.showPlayingFormat = true;
                            $scope.playingFormatSrc = '../static/img/logo-mp3.png';
                        } else {
                            $scope.showPlayingFormat = false;
                        }
                    } else {
                        $scope.showPlayingFormat = false;
                    }
                });
            }
        }
    })
;
