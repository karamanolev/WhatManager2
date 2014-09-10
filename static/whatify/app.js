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
                return $http.get('torrent_groups/search/' +
                        encodeURIComponent(query), {timeout: this.searchTorrentGroupsCanceller.promise}
                );
            };
            this.getTorrentGroup = function (id) {
                return $http.get('torrent_groups/' + id);
            };
            this.searchArtistsCanceller = null;
            this.searchArtists = function (query) {
                if (this.searchArtistsCanceller) {
                    this.searchArtistsCanceller.resolve('New search coming');
                }
                this.searchArtistsCanceller = $q.defer();
                return $http.get('artists/search/' +
                        encodeURIComponent(query), {timeout: this.searchArtistsCanceller.promise}
                );
            };
            this.getArtist = function (id) {
                return $http.get('artists/' + id);
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
