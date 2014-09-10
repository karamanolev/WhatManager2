'use strict';

angular.
    module('whatify.home', ['ngRoute']).
    config(function ($routeProvider) {
        $routeProvider.
            when('/', {
                templateUrl: 'home/home.html',
                controller: 'HomeController'
            }).
            when('/torrentGroups/:id', {
                templateUrl: 'home/torrentGroup.html',
                controller: 'TorrentGroupController'
            }).
            when('/artists/:id', {
                templateUrl: 'home/artist.html',
                controller: 'ArtistController'
            }).
            when('/playlist', {
                templateUrl: 'home/playlist.html',
                controller: 'WhatPlayerController'
            })
    }).
    controller('HomeController', function ($scope) {
    }).
    controller('TorrentGroupController', function ($scope, WhatMeta, $routeParams) {
        WhatMeta.getTorrentGroup($routeParams.id).success(function (torrentGroup) {
            $scope.torrentGroup = torrentGroup;
        });
    }).
    controller('ArtistController', function ($scope, WhatMeta, $routeParams) {
        WhatMeta.getArtist($routeParams.id).success(function (artist) {
            $scope.artist = artist;
        });
    })
;
