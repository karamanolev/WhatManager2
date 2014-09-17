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
    controller('TorrentGroupController', function($scope, $interval, $routeParams, whatMeta, whatifyNoty) {
        var refreshInterval = null,
            subscribe = function() {
                if (refreshInterval === null) {
                    refreshInterval = $interval(function() {
                        $scope.reloadTorrentGroup(false, true);
                    }, 3000);
                }
            },
            unsubscribe = function() {
                if (refreshInterval !== null) {
                    $interval.cancel(refreshInterval);
                    refreshInterval = null;
                }
            };
        $scope.reloadTorrentGroup = function(initial, defeatCache, loadFromWhat) {
            if (initial) {
                $scope.torrentGroup = null;
                $scope.mainSpinner.visible = true;
            }
            whatMeta.getTorrentGroup($routeParams.id, defeatCache, loadFromWhat)
                .success(function(torrentGroup) {
                    $scope.torrentGroup = torrentGroup;
                    if ($scope.torrentGroup.have !== undefined) {
                        subscribe();
                    } else if ($scope.torrentGroup.have === undefined) {
                        unsubscribe();
                    }
                    $scope.mainSpinner.visible = false;
                });
        };
        $scope.downloadTorrentGroup = function(torrentGroupId) {
            if (confirm('Are you sure you want to download this?')) {
                whatMeta.downloadTorrentGroup($scope.torrentGroup.id).success(function(resp) {
                    if (resp.success) {
                        whatifyNoty.success('Downloading ' + $scope.torrentGroup.name);
                    }
                });
                subscribe();
            }
        };
        $scope.$on('$destroy', function() {
            unsubscribe();
        });
        $scope.reloadTorrentGroup(true);
    }).
    controller('ArtistController', function($scope, whatMeta, $routeParams) {
        $scope.reloadArtist = function(defeatCache, loadFromWhat) {
            $scope.artist = null;
            $scope.mainSpinner.visible = true;
            whatMeta.getArtist($routeParams.id, defeatCache, loadFromWhat)
                .success(function(artist) {
                    $scope.artist = artist;
                    $scope.mainSpinner.visible = false;
                });
        };
        $scope.reloadArtist();
    })
;
