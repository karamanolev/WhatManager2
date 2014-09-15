'use strict';

angular.
    module('whatify', [
        'ngRoute',
        'whatify.home',
        'whatify.player',
        'whatify.searchBar'
    ]).
    factory('whatMeta', function($q, $http) {
        return new function() {
            this.getTorrentGroup = function(id) {
                return $http.get('torrent_groups/' + id);
            };
            this.searchCanceller = null;
            this.search = function(query) {
                if (this.searchCanceller) {
                    this.searchCanceller.resolve('New search coming');
                }
                this.searchCanceller = $q.defer();
                return $http.get('search/' +
                        encodeURIComponent(query), {timeout: this.searchCanceller.promise}
                );
            };
            this.getArtist = function(id) {
                return $http.get('artists/' + id);
            };
        };
    }).
    filter('trustAsHtml', function($sce) {
        return function(input) {
            return $sce.trustAsHtml(input);
        };
    }).
    filter('asPercent', function() {
        return function(value) {
            return Math.floor(value * 100) + '%';
        };
    }).
    filter('asTime', function() {
        return function(value) {
            if (value === null) {
                return '-:--';
            }
            var seconds = Math.floor(value % 60);
            var minutes = Math.floor(value / 60);
            return minutes + ':' + (seconds < 10 ? '0' + seconds : seconds);
        }
    }).
    config(function($routeProvider) {
        $routeProvider.otherwise({redirectTo: '/'})
    })
;
