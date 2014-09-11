'use strict';

angular.
    module('whatify.player', []).
    factory('WhatPlayerService', function ($rootScope) {
        return new function () {
            var service = this;
            window.service = this;
            this.audio = document.createElement('audio');
            this.currentItem = null;
            this.isPlaying = false;
            this.currentTime = 0;
            this.duration = 0;
            this.playlist = [];
            this.playlistIndex = 0;

            $(this.audio).on('playing', function () {
                $rootScope.$apply(function () {
                    service.isPlaying = true;
                });
            });
            $(this.audio).on('timeupdate', function () {
                $rootScope.$apply(function () {
                    service.currentTime = service.audio.currentTime;
                });
            });
            $(this.audio).on('loadedmetadata', function () {
                $rootScope.$apply(function () {
                    service.duration = service.audio.duration;
                });
            });
            $(this.audio).on('ended', function () {
                $rootScope.$apply(function () {
                    if (service.playlistIndex < service.playlist.length - 1) {
                        service.play(service.playlistIndex + 1);
                    } else {
                        service.goTo(0);
                    }
                });
            });
            $(this.audio).on('error', function () {
                $rootScope.$apply(function () {
                    service.isPlaying = false;
                });
            });
            this.goTo = function (index) {
                this.playlistIndex = index;
                this.currentItem = this.playlist[this.playlistIndex];
                this.audio.src = this.currentItem.url;
                this.currentTime = 0;
                this.duration = 0;
                this.isPlaying = false;
            };
            this.play = function (index) {
                console.log('Called play ' + index);
                if (index != undefined) {
                    this.goTo(index);
                }
                this.isPlaying = true;
                this.audio.play();
            };
            this.pause = function () {
                this.isPlaying = false;
                this.audio.pause();
            };
            this.playlistClear = function () {
                this.playlist = [];
                this.playlistIndex = -1;
                this.audio.pause();
                this.audio.src = '';
                this.currentItem = null;
                this.currentTime = 0;
                this.duration = 0;
                this.isPlaying = false;
            };
            this.playlistAdd = function (item) {
                this.playlist.push(item);
            };
            this.setVolume = function(volume) {
                this.audio.volume = volume;
            };
            this.getVolume = function() {
                return this.audio.volume;
            };
        };
    }).
    controller('WhatPlayerController', function ($scope, WhatMeta, WhatPlayerService) {
        $scope.player = WhatPlayerService;
        $scope.playTorrentGroup = function (torrentGroupId, index) {
            WhatMeta.getTorrentGroup(torrentGroupId).success(function (torrentGroup) {
                var inPlaylist = false;
                if (index != undefined) {
                    $.each(WhatPlayerService.playlist, function (i, item) {
                        if (item.id == torrentGroup.playlist[index].id) {
                            WhatPlayerService.play(i);
                            inPlaylist = true;
                            return false;
                        }
                    });
                }
                if (!inPlaylist) {
                    WhatPlayerService.playlistClear();
                    $.each(torrentGroup.playlist, function (i, item) {
                        WhatPlayerService.playlistAdd(item);
                    });
                    WhatPlayerService.play(index || 0);
                }
            });
        };
    }).
    directive('ngWmPlayerSm', function () {
        return {
            'templateUrl': templateRoot + '/player/player.html',
            'controller': 'WhatPlayerController'
        }
    })
;
