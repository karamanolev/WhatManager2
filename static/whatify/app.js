'use strict';

angular.
    module('whatify', [
        'ngRoute',
        'whatify.home',
        'whatify.player',
        'whatify.searchBar'
    ]).
    factory('WhatMeta', function ($q, $http) {
        return new function () {
            this.searchTorrentGroupsCanceller = null;
            this.searchTorrentGroups = function (query) {
                if (this.searchTorrentGroupsCanceller) {
                    this.searchTorrentGroupsCanceller.resolve('New search coming');
                }
                this.searchTorrentGroupsCanceller = $q.defer();
                return $http.get('http://localhost:8000/what_meta/torrent_groups/search/' +
                        encodeURIComponent(query), {timeout: this.searchTorrentGroupsCanceller.promise}
                );
            };
            this.getTorrentGroup = function (id) {
                return $http.get('http://localhost:8000/what_meta/torrent_groups/' + id);
            };
            this.searchArtistsCanceller = null;
            this.searchArtists = function (query) {
                if (this.searchArtistsCanceller) {
                    this.searchArtistsCanceller.resolve('New search coming');
                }
                this.searchArtistsCanceller = $q.defer();
                return $http.get('http://localhost:8000/what_meta/artists/search/' +
                        encodeURIComponent(query), {timeout: this.searchArtistsCanceller.promise}
                );
            };
            this.getArtist = function (id) {
                return $http.get('http://localhost:8000/what_meta/artists/' + id);
            };
            this.getPlaylist = function (playlist) {
                var defer = $q.defer();
                setTimeout(function () {
                    defer.resolve([
                        {
                            url: 'https://karamanolev.com/wm/player/file?path=%2Fmnt%2Fshark%2FTorrent%2FWhat.CD%2F31638596%2FMachinae%20Supremacy%20-%20Phantom%20Shadow%20-%202014%20(CD%20-%20MP3%20-%20V0)%2F01.%20Machinae%20Supremacy%20-%20I%20wasn%27t%20made%20for%20the%20world%20I%20left%20behind.mp3',
                            title: 'Machinae Supremacy - I wasn\'t made for the world I left behind'
                        }
                    ]);
                }, 1);
                return defer.promise;
            };
        };
    }).
    filter('trustAsHtml', function ($sce) {
        return function (input) {
            return $sce.trustAsHtml(input);
        };
    }).
    config(function ($routeProvider) {
        $routeProvider.otherwise({redirectTo: '/'})
    });
