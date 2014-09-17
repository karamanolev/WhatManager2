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
    controller('TorrentGroupController', function($scope, $interval, whatMeta, $routeParams) {
        var refreshInterval = null;
        $scope.reloadTorrentGroup = function(initial, defeatCache, loadFromWhat) {
            if(initial) {
                $scope.torrentGroup = null;
                $scope.mainSpinner.visible = true;
            }
            whatMeta.getTorrentGroup($routeParams.id, defeatCache, loadFromWhat)
                .success(function(torrentGroup) {
                    $scope.torrentGroup = torrentGroup;
                    if (refreshInterval === null && $scope.torrentGroup.have !== undefined) {
                        console.log('subscribing');
                        refreshInterval = $interval(function() {
                            console.log('update called');
                            $scope.reloadTorrentGroup(false, true);
                        }, 3000);
                    } else if (refreshInterval !== null && $scope.torrentGroup.have === undefined) {
                        console.log('downloaded, unsubscribing');
                        $interval.cancel(refreshInterval);
                        refreshInterval = null;
                    }
                    $scope.mainSpinner.visible = false;
                });
        };
        $scope.$on('$destroy', function() {
            if (refreshInterval !== null) {
                console.log('unsubscribing');
                $interval.cancel(refreshInterval);
                refreshInterval = null;
            }
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
