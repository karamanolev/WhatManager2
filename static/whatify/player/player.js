'use strict';

angular.
    module('whatify.player', []).
    factory('whatPlayer', function($rootScope) {
        var s = {};
        s.audio = document.createElement('audio');
        s.isPlaying = false;
        s.currentTime = 0;
        s.duration = null;

        s.aurora = null;

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
            $rootScope.$emit('songEnded');
        }

        function bindAurora() {
            s.aurora.on('duration', auroraDuration);
            s.aurora.on('progress', auroraProgress);
            s.aurora.on('end', auroraEnd);
        }

        function unbindAurora() {
            s.aurora.off('duration', auroraDuration);
            s.aurora.off('progress', auroraProgress);
            s.aurora.off('end', auroraEnd);
        }

        $(s.audio).on('playing', function() {
            console.log('<audio>: playing');
            $rootScope.$apply(function() {
                s.isPlaying = true;
            });
        });
        $(s.audio).on('timeupdate', function() {
            console.log('<audio>: timeupdate');
            $rootScope.$apply(function() {
                s.currentTime = s.audio.currentTime;
            });
        });
        $(s.audio).on('loadedmetadata', function() {
            console.log('<audio>: loadedmetadata');
            $rootScope.$apply(function() {
                s.duration = s.audio.duration;
            });
        });
        $(s.audio).on('ended', function() {
            console.log('<audio>: ended');
            $rootScope.$emit('songEnded');
        });
        $(s.audio).on('error', function(e) {
            console.log('<audio>: error');
            $rootScope.$apply(function() {
                s.isPlaying = false;
            });
        });
        s.play = function() {
            if (s.audio.src) {
                s.audio.play();
                s.isPlaying = true;
            } else if (s.aurora !== null) {
                s.aurora.play();
                s.isPlaying = true;
            }
        };
        s.load = function(src) {
            if (s.aurora !== null) {
                s.aurora.stop();
                unbindAurora();
                s.aurora = null;
            }
            if (s.audio.src) {
                s.audio.pause();
                s.audio.src = '';
                s.audio.removeAttribute('src');
            }
            s.isPlaying = false;
            s.currentTime = 0;
            s.duration = null;
            if (src) {
                if (src.toLowerCase().indexOf('.flac') != -1) {
                    s.aurora = AV.Player.fromURL(src);
                    bindAurora();
                } else if (src.toLowerCase().indexOf('.mp3') != -1) {
                    s.audio.src = src;
                } else {
                    console.error('Neither .mp3 nor .flac found in URL.');
                }
            }
        };
        s.pause = function() {
            if (s.audio.src) {
                s.isPlaying = false;
                s.audio.pause();
            } else if (s.aurora !== null) {
                s.isPlaying = false;
                s.aurora.pause();
            }
        };
        s.setVolume = function(volume) {
            s.audio.volume = volume;
            if (s.aurora !== null) {
                s.aurora.volume = Math.round(volume * 100);
            }
        };
        s.getVolume = function() {
            return s.audio.volume;
        };
        s.seek = function(time) {
            s.audio.currentTime = time;
        };
        return s;
    }).
    factory('whatPlaylist', function($rootScope, whatPlayer) {
        var s = {
            items: [],
            index: -1
        };
        var update = function() {
            if (s.index == -1) {
                s.currentItem = null;
            } else {
                s.currentItem = s.items[s.index];
            }
            s.canForward = s.index != -1 && s.index < s.items.length - 1;
            s.canBackward = s.index > 0;
        };
        update();

        $rootScope.$on('songEnded', function() {
            if (s.canForward) {
                s.play(s.index + 1);
            } else {
                s.index = 0;
                update();
                whatPlayer.load(s.currentItem.url);
            }
        });
        s.clear = function() {
            s.items = [];
            s.index = -1;
            update();
            whatPlayer.load(null);
        };
        s.play = function(index) {
            s.index = index;
            update();
            whatPlayer.load(s.currentItem.url);
            whatPlayer.play();
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
    controller('WhatPlayerController', function($scope, whatMeta, whatPlayer, whatPlaylist) {
        $scope.player = whatPlayer;
        $scope.playlist = whatPlaylist;
        $scope.volume = whatPlayer.getVolume();
        $scope.$watch('volume', function(newValue) {
            whatPlayer.setVolume(newValue);
        });
        $scope.seek = function(time) {
            whatPlayer.seek(time);
        };

        $scope.playTorrentGroup = function(torrentGroupId, index) {
            if (whatPlaylist.currentItem &&
                whatPlaylist.currentItem.torrentGroup.id == torrentGroupId) {
                if (index === undefined) {
                    whatPlayer.play();
                    return;
                }
            }
            whatMeta.getTorrentGroup(torrentGroupId).success(function(torrentGroup) {
                var inPlaylist = false;
                if (index !== undefined) {
                    $.each(whatPlaylist.items, function(i, item) {
                        if (item.id == torrentGroup.playlist[index].id) {
                            whatPlaylist.play(i);
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
                    whatPlaylist.play(index || 0);
                }
            });
        };
    }).
    directive('wmPlayerSm', function() {
        return {
            templateUrl: templateRoot + '/player/player.html',
            controller: 'WhatPlayerController'
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
                scope.$watch(function() {
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
    })
;
