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
            this.getTorrentGroup = function (id) {
                return $http.get('torrent_groups/' + id);
            };
            this.searchCanceller = null;
            this.search = function (query) {
                if (this.searchCanceller) {
                    this.searchCanceller.resolve('New search coming');
                }
                this.searchCanceller = $q.defer();
                return $http.get('search/' +
                        encodeURIComponent(query), {timeout: this.searchCanceller.promise}
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
