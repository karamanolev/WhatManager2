'use strict';

angular.
    module('whatify.home', ['ngRoute']).
    config(function($routeProvider) {
        $routeProvider.
            when('/', {
                templateUrl: templateRoot + '/home/home.html',
                controller: 'HomeController'
            }).
            when('/torrentGroups/:id', {
                templateUrl: templateRoot + '/home/torrentGroup.html',
                controller: 'TorrentGroupController'
            }).
            when('/torrentGroups/:id/play', {
                template: '',
                controller: 'PlayTorrentGroupController'
            }).
            when('/torrentGroups/:id/play/:index', {
                template: '',
                controller: 'PlayTorrentGroupController'
            }).
            when('/artists/:id', {
                templateUrl: templateRoot + '/home/artist.html',
                controller: 'ArtistController'
            }).
            when('/playlist', {
                templateUrl: templateRoot + '/home/playlist.html',
                controller: 'PlaylistController'
            })
    }).
    controller('HomeController', function($scope) {
        $scope.mainSpinner.visible = false;
    }).
    controller('PlaylistController', function($scope) {
        $scope.mainSpinner.visible = false;
    }).
    controller('PlayTorrentGroupController', function($scope, $location, $routeParams, whatMeta) {
        whatMeta.getTorrentGroup($routeParams.id, false, false).success(function(torrentGroup) {
            if (torrentGroup.playlist !== undefined) {
                $scope.playTorrentGroup(torrentGroup, $routeParams.index);
            }
            $location.path('/torrentGroups/' + $routeParams.id);
        });
    }).
    controller('TorrentGroupController', function($scope, $interval, $routeParams, whatMeta, whatifyNoty) {
        var refreshInterval = null;
        $scope.subscribe = function() {
            if (refreshInterval === null) {
                refreshInterval = $interval(function() {
                    $scope.reloadTorrentGroup(false, true);
                }, 3000);
            }
        };
        $scope.unsubscribe = function() {
            if (refreshInterval !== null) {
                $interval.cancel(refreshInterval);
                refreshInterval = null;
            }
        };
        $scope.$on('torrentDownloading', $scope.subscribe);
        $scope.reloadTorrentGroup = function(initial, defeatCache, loadFromWhat) {
            if (initial) {
                $scope.torrentGroup = null;
                $scope.mainSpinner.visible = true;
            }
            whatMeta.getTorrentGroup($routeParams.id, defeatCache, loadFromWhat)
                .success(function(torrentGroup) {
                    $scope.torrentGroup = torrentGroup;
                    if (angular.isNumber($scope.torrentGroup.have)) {
                        $scope.subscribe();
                    } else if ($scope.torrentGroup.have === true) {
                        $scope.unsubscribe();
                    }
                    $scope.mainSpinner.visible = false;
                });
        };
        $scope.$on('$destroy', function() {
            $scope.unsubscribe();
        });
        $scope.reloadTorrentGroup(true);
    }).
    controller('ArtistController', function($scope, $interval, whatMeta, $routeParams) {
        var refreshInterval = null;
        var showArtist = function(artist) {
            var hasInProgress;
            $.each(artist.torrent_groups, function(i, section) {
                $.each(section, function(j, torrentGroup) {
                    if (angular.isNumber(torrentGroup.have)) {
                        hasInProgress = true;
                        return false;
                    }
                });
                if (hasInProgress) {
                    return false;
                }
            });
            if (hasInProgress) {
                $scope.subscribe();
            } else {
                $scope.unsubscribe();
            }
            $scope.artist = artist;
            $scope.mainSpinner.visible = false;
        };
        $scope.subscribe = function() {
            console.log('subscribe');
            if (refreshInterval === null) {
                refreshInterval = $interval(function() {
                    $scope.updateProgress(false, true);
                }, 3000);
            }
        };
        $scope.unsubscribe = function() {
            if (refreshInterval !== null) {
                $interval.cancel(refreshInterval);
                refreshInterval = null;
            }
        };
        $scope.$on('torrentDownloading', $scope.subscribe);
        $scope.updateProgress = function() {
            var groupById = {};
            $.each($scope.artist.torrent_groups, function(i, section) {
                $.each(section, function(j, torrentGroup) {
                    groupById[torrentGroup.id] = torrentGroup;
                });
            });
            whatMeta.getArtist($routeParams.id, true, false).success(function(artist) {
                var needsShow = false;
                $.each(artist.torrent_groups, function(i, section) {
                    $.each(section, function(j, newGroup) {
                        var oldGroup = groupById[newGroup.id];
                        if (oldGroup === undefined) {
                            needsShow = true;
                            return false;
                        }
                        if (angular.isNumber(oldGroup.have) && angular.isNumber(newGroup.have)) {
                            oldGroup.have = newGroup.have;
                        } else if (oldGroup.have !== newGroup.have) {
                            needsShow = true;
                            return false;
                        }
                    });
                    if (needsShow) {
                        return false;
                    }
                });
                if (needsShow) {
                    showArtist(artist);
                }
            });
        };
        $scope.reloadArtist = function(initial, defeatCache, loadFromWhat) {
            if (initial) {
                $scope.artist = null;
                $scope.mainSpinner.visible = true;
            }
            whatMeta.getArtist($routeParams.id, defeatCache, loadFromWhat).success(function(artist) {
                showArtist(artist);
            });
        };
        $scope.reloadArtist(true);
        $scope.$on('$destroy', function() {
            $scope.unsubscribe();
        });
    }).
    directive('albumInfo', function() {
        return {
            templateUrl: templateRoot + '/home/albumInfo.html',
            scope: {
                torrentGroup: '=',
                size: '='
            },
            transclude: true,
            controller: 'WhatPlayerController',
            link: function(scope, element, attrs) {
                if (attrs.linkTitle !== undefined) {
                    scope.linkTitle = true;
                }
            }
        }
    }).
    directive('artistInfo', function() {
        return {
            templateUrl: templateRoot + '/home/artistInfo.html',
            scope: {
                artist: '=',
                size: '='
            }
        }
    }).
    directive('albumPlaylist', function() {
        return {
            templateUrl: templateRoot + '/home/albumPlaylist.html',
            controller: 'WhatPlayerController',
            scope: {
                torrentGroup: '='
            }
        }
    }).
    directive('squareImage', function() {
        return {
            template: '<div class="square-cover"><div class="cover-image"></div></div>',
            scope: {
                src: '='
            },
            replace: true,
            link: function(scope, element, attrs) {
                var cover = element.find('.cover-image');
                attrs.$observe('size', function() {
                    var size = attrs.size || '';
                    cover.css('width', size);
                    cover.css('height', size);
                });
                scope.$watch('src', function(newValue) {
                    cover.css('background-image', "url('" + newValue + "')");
                });
            }
        }
    })
;
