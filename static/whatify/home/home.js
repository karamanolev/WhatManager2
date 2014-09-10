'use strict';

angular.
    module('whatify.home', ['ngRoute']).
    config(function ($routeProvider) {
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
