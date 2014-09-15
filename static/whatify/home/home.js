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
                controller: 'WhatPlayerController'
            })
    }).
    controller('HomeController', function($scope) {
    }).
    controller('TorrentGroupController', function($scope, whatMeta, $routeParams) {
        $scope.reloadTorrentGroup = function(defeatCache) {
            $scope.torrentGroup = null;
            $scope.mainSpinner.visible = true;
            whatMeta.getTorrentGroup($routeParams.id, defeatCache).success(function(torrentGroup) {
                $scope.torrentGroup = torrentGroup;
                $scope.mainSpinner.visible = false;
            });
        };
        $scope.reloadTorrentGroup();
    }).
    controller('ArtistController', function($scope, whatMeta, $routeParams) {
        $scope.reloadArtist = function(defeatCache) {
            $scope.artist = null;
            $scope.mainSpinner.visible = true;
            whatMeta.getArtist($routeParams.id, defeatCache).success(function(artist) {
                $scope.artist = artist;
                $scope.mainSpinner.visible = false;
            });
        };
        $scope.reloadArtist();
    })
;
